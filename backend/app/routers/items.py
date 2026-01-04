from uuid import UUID
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query, Request, File, UploadFile, Form
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.item import ItemCreate, ItemUpdate, ItemResponse, ProgressUpdate, ProgressHistoryResponse
from app.schemas.project import ProjectSectionResponse
from app.services.item_service import (
    create_item,
    get_item,
    list_items,
    update_item,
    delete_item,
    update_progress,
    get_progress_history,
)
from app.services.import_service import import_items_from_files
from app.services.audit_service import log_action
from app.services.notification_service import notify_item_updated
from app.dependencies import get_current_user, require_role
from app.models.user import User, UserRole
from app.models.item import Item
from app.models.project_section import ProjectSection

router = APIRouter()


def item_to_response(item: Item) -> ItemResponse:
    """Convert Item model to ItemResponse with original_filename from current revision."""
    # Get original_filename from first document's current revision if exists
    original_filename = None
    if item.documents:
        for doc in item.documents:
            if hasattr(doc, 'current_revision') and doc.current_revision:
                original_filename = doc.current_revision.original_filename
                break
            elif hasattr(doc, 'revisions') and doc.revisions:
                # Find current revision
                for rev in doc.revisions:
                    if rev.is_current:
                        original_filename = rev.original_filename
                        break
                if original_filename:
                    break
    
    # Build section response if exists
    section_response = None
    if item.section:
        section_response = ProjectSectionResponse.model_validate(item.section)
    
    response = ItemResponse.model_validate(item)
    response.original_filename = original_filename
    response.section = section_response
    return response


@router.get("", response_model=List[ItemResponse])
async def get_items(
    project_id: Optional[UUID] = Query(None),
    section_id: Optional[UUID] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    items = list_items(db, project_id=project_id, section_id=section_id)
    return [item_to_response(i) for i in items]


@router.post("", response_model=ItemResponse)
async def create_new_item(
    request: Request,
    item_data: ItemCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin"]))
):
    item = create_item(db, item_data)
    
    # Audit log
    log_action(
        db,
        user_id=current_user.id,
        action_type="item.create",
        payload={"item_id": str(item.id), "part_number": item.part_number, "name": item.name},
        ip_address=getattr(request.state, "ip", None)
    )
    
    return item_to_response(item)


@router.get("/{item_id}", response_model=ItemResponse)
async def get_item_by_id(
    item_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    item = get_item(db, item_id)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")
    return item_to_response(item)


@router.patch("/{item_id}", response_model=ItemResponse)
async def update_item_by_id(
    request: Request,
    item_id: UUID,
    item_data: ItemUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin"]))
):
    # Get item before update to capture old values
    item = get_item(db, item_id)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")
    
    # Validate section_id if provided
    changes = item_data.model_dump(exclude_unset=True)
    if "section_id" in changes and changes["section_id"] is not None:
        section = db.query(ProjectSection).filter(
            ProjectSection.id == changes["section_id"]
        ).first()
        if not section:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Section not found"
            )
        if section.project_id != item.project_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Section belongs to a different project"
            )
    
    # Save old values before update
    old_values = {field: getattr(item, field) for field in changes.keys()}
    
    # Update item
    updated_item = update_item(db, item_id, item_data)
    
    # Get new values after update
    new_values = changes.copy()
    
    # Audit log with old/new values
    log_action(
        db,
        user_id=current_user.id,
        action_type="item.update",
        payload={
            "item_id": str(item_id),
            "changes": jsonable_encoder(changes),
            "old_values": jsonable_encoder(old_values),
            "new_values": jsonable_encoder(new_values)
        },
        ip_address=getattr(request.state, "ip", None)
    )
    
    # Notify if section_id changed
    if "section_id" in changes:
        notify_item_updated(
            db,
            updated_item,
            jsonable_encoder(old_values),
            jsonable_encoder(new_values),
            current_user.id
        )
    
    return item_to_response(updated_item)


@router.patch("/{item_id}/progress", response_model=ItemResponse)
async def update_item_progress(
    request: Request,
    item_id: UUID,
    progress_data: ProgressUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    item = get_item(db, item_id)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")
    
    # RBAC: admin or responsible user
    if current_user.role != UserRole.admin and item.responsible_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to update progress")
    
    old_progress = item.current_progress
    updated_item = update_progress(db, item_id, progress_data.new_progress, current_user.id, progress_data.comment)
    
    # Audit log
    log_action(
        db,
        user_id=current_user.id,
        action_type="item.progress_update",
        payload={
            "item_id": str(item_id),
            "old_progress": old_progress,
            "new_progress": progress_data.new_progress,
            "comment": progress_data.comment
        },
        ip_address=getattr(request.state, "ip", None)
    )
    
    return item_to_response(updated_item)


@router.delete("/{item_id}")
async def delete_item_by_id(
    request: Request,
    item_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin"]))
):
    success = delete_item(db, item_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")
    
    # Audit log
    log_action(
        db,
        user_id=current_user.id,
        action_type="item.delete",
        payload={"item_id": str(item_id)},
        ip_address=getattr(request.state, "ip", None)
    )
    
    return {"message": "Item deleted"}


@router.get("/{item_id}/progress-history", response_model=List[ProgressHistoryResponse])
async def get_item_progress_history(
    item_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    history = get_progress_history(db, item_id)
    return [ProgressHistoryResponse.model_validate(h) for h in history]


@router.post("/import")
async def import_items(
    request: Request,
    project_id: UUID = Form(...),
    files: List[UploadFile] = File(...),
    section_id: Optional[UUID] = Form(None),
    responsible_id: Optional[UUID] = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin"]))
):
    """
    Import items from uploaded PDF files.
    
    RBAC: admin only
    
    Returns:
        {"created_count": int, "errors": List[{"filename": str, "error": str}]}
    """
    result = await import_items_from_files(
        db=db,
        project_id=project_id,
        files=files,
        section_id=section_id,
        responsible_id=responsible_id,
        current_user=current_user,
    )
    
    # Log audit action for each created item
    if result["created_count"] > 0:
        log_action(
            db,
            user_id=current_user.id,
            action_type="item.import",
            payload={
                "project_id": str(project_id),
                "created_count": result["created_count"],
                "errors_count": len(result["errors"]),
            },
            ip_address=getattr(request.state, "ip", None)
        )
    
    return result

