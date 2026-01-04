from uuid import UUID
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File, Form, Request
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.document import DocumentCreate, RevisionCreate, DocumentResponse, RevisionResponse
from app.services.document_service import (
    create_document,
    get_document,
    list_documents,
    upload_revision,
    soft_delete_document,
    hard_delete_document,
    get_revision_file_path,
)
from app.services.notification_service import notify_document_deleted
from app.services.item_service import get_item
from app.services.audit_service import log_action
from app.dependencies import get_current_user, require_role
from app.models.user import User, UserRole

router = APIRouter()


@router.get("", response_model=List[DocumentResponse])
async def get_documents(
    item_id: Optional[UUID] = Query(None),
    show_deleted: Optional[bool] = Query(False),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if show_deleted and current_user.role != UserRole.admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only admins can view deleted documents")
    documents = list_documents(db, item_id=item_id, show_deleted=show_deleted)
    return [DocumentResponse.model_validate(d) for d in documents]


@router.post("", response_model=DocumentResponse)
async def create_new_document(
    request: Request,
    item_id: UUID = Form(...),
    title: str = Form(...),
    type: Optional[str] = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Check item exists and RBAC
    item = get_item(db, item_id)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")
    
    # RBAC: admin or responsible user
    if current_user.role != UserRole.admin and item.responsible_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to upload documents")
    
    document = await create_document(db, item_id, title, type, file, current_user.id)
    
    # Audit log
    log_action(
        db,
        user_id=current_user.id,
        action_type="document.create",
        payload={
            "document_id": str(document.id),
            "item_id": str(item_id),
            "title": title,
            "original_filename": file.filename
        },
        ip_address=getattr(request.state, "ip", None)
    )
    
    return DocumentResponse.model_validate(document)


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document_by_id(
    document_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    document = get_document(db, document_id)
    if not document:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    if document.is_deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    return DocumentResponse.model_validate(document)


@router.post("/{document_id}/revisions", response_model=RevisionResponse)
async def upload_new_revision(
    request: Request,
    document_id: UUID,
    change_note: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    document = get_document(db, document_id)
    if not document:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    
    # Get item for RBAC
    item = get_item(db, document.item_id)
    
    # RBAC: admin or responsible user
    if current_user.role != UserRole.admin and item.responsible_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to upload revisions")
    
    revision = await upload_revision(db, document_id, file, change_note, current_user.id)
    
    # Audit log
    log_action(
        db,
        user_id=current_user.id,
        action_type="document.revision_upload",
        payload={
            "document_id": str(document_id),
            "revision_id": str(revision.id),
            "revision_label": revision.revision_label,
            "change_note": change_note,
            "original_filename": file.filename
        },
        ip_address=getattr(request.state, "ip", None)
    )
    
    return RevisionResponse.model_validate(revision)


@router.get("/{document_id}/revisions/{revision_id}/download")
async def download_revision(
    document_id: UUID,
    revision_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    document = get_document(db, document_id)
    if not document or document.is_deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    file_info = get_revision_file_path(db, document_id, revision_id)
    if not file_info:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Revision not found")
    
    path, filename = file_info
    return FileResponse(path, filename=filename, media_type="application/pdf")


@router.get("/{document_id}/revisions/{revision_id}/preview")
async def preview_revision(
    document_id: UUID,
    revision_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    document = get_document(db, document_id)
    if not document or document.is_deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    file_info = get_revision_file_path(db, document_id, revision_id)
    if not file_info:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Revision not found")
    
    path, _ = file_info
    
    def iterfile():
        with open(path, mode="rb") as f:
            yield from f
    
    return StreamingResponse(iterfile(), media_type="application/pdf")


@router.delete("/{document_id}")
async def delete_document_by_id(
    request: Request,
    document_id: UUID,
    hard: bool = Query(False),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Get document
    document = get_document(db, document_id)
    if not document:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    
    # Get item for RBAC
    item = get_item(db, document.item_id)
    
    # RBAC check
    if hard:
        # Hard delete: only admin
        if current_user.role != UserRole.admin:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only admins can hard delete documents")
    else:
        # Soft delete: admin or responsible for their item
        if current_user.role != UserRole.admin and item.responsible_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to delete this document")
    
    # Store old state for audit
    old_state = {"is_deleted": document.is_deleted}
    
    # Perform deletion
    if hard:
        success = hard_delete_document(db, document_id)
        mode = "hard"
    else:
        soft_delete_document(db, document_id, current_user.id)
        mode = "soft"
    
    # Notify
    notify_document_deleted(db, document, item, mode)
    
    # Audit log
    log_action(
        db,
        user_id=current_user.id,
        action_type="document.delete",
        payload={
            "document_id": str(document_id),
            "item_id": str(document.item_id),
            "title": document.title,
            "mode": mode,
            "old_state": old_state
        },
        ip_address=getattr(request.state, "ip", None)
    )
    
    return {"message": "Document deleted", "mode": mode}

