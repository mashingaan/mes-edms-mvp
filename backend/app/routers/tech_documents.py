from uuid import UUID
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Request, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.tech_document import (
    TechDocumentResponse,
    TechDocumentUploadResponse,
    TechDocumentVersionResponse,
    TechDocumentPreviewResponse,
)
from app.services.tech_document_service import (
    list_documents,
    upload_document,
    get_document,
    update_document,
    delete_document,
    list_versions,
)
from app.services.file_storage_service import get_excel_file_path
from app.services.excel_preview_service import generate_preview
from app.services.notification_service import (
    notify_tech_document_uploaded,
    notify_tech_document_updated,
    notify_tech_document_deleted,
)
from app.services.audit_service import log_action
from app.dependencies import get_current_user, require_role
from app.models.user import User
from app.models.project_section import ProjectSection
from app.utils.validators import validate_excel_file

router = APIRouter()


def get_section(db: Session, section_id: UUID) -> ProjectSection:
    section = db.query(ProjectSection).filter(ProjectSection.id == section_id).first()
    if not section:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Section not found")
    return section


@router.get("/sections/{section_id}/documents", response_model=List[TechDocumentResponse])
def get_section_documents(
    section_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    get_section(db, section_id)
    documents = list_documents(db, section_id)
    return [TechDocumentResponse.model_validate(doc) for doc in documents]


@router.post("/sections/{section_id}/documents", response_model=TechDocumentUploadResponse)
async def upload_section_document(
    request: Request,
    section_id: UUID,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin"]))
):
    section = get_section(db, section_id)
    await validate_excel_file(file)

    document = await upload_document(db, section_id, file, current_user.id)

    notify_tech_document_uploaded(db, document, section)

    log_action(
        db,
        user_id=current_user.id,
        action_type="tech_document.upload",
        payload={
            "document_id": str(document.id),
            "section_id": str(section_id),
            "version": document.version,
        },
        ip_address=getattr(request.state, "ip", None)
    )

    return TechDocumentUploadResponse.model_validate(document)


@router.get("/documents/{document_id}", response_model=TechDocumentResponse)
def get_document_by_id(
    document_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    document = get_document(db, document_id)
    if not document or document.is_deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    return TechDocumentResponse.model_validate(document)


@router.get("/documents/{document_id}/download")
def download_document(
    document_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    document = get_document(db, document_id)
    if not document or document.is_deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    path = get_excel_file_path(document.storage_uuid, document.file_extension)
    if not path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")

    return FileResponse(path, filename=document.filename, media_type="application/octet-stream")


@router.get("/documents/{document_id}/preview", response_model=TechDocumentPreviewResponse)
def preview_document(
    document_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    document = get_document(db, document_id)
    if not document or document.is_deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    path = get_excel_file_path(document.storage_uuid, document.file_extension)
    if not path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")

    preview_data = generate_preview(path)
    return TechDocumentPreviewResponse(
        filename=document.filename,
        sheets=preview_data.get("sheets", [])
    )


@router.put("/documents/{document_id}", response_model=TechDocumentUploadResponse)
async def update_document_by_id(
    request: Request,
    document_id: UUID,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin"]))
):
    document = get_document(db, document_id)
    if not document or document.is_deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    section = get_section(db, document.section_id)
    old_version = document.version

    await validate_excel_file(file)
    updated_document = await update_document(db, document_id, file, current_user.id)

    notify_tech_document_updated(db, updated_document, section, old_version, updated_document.version)

    log_action(
        db,
        user_id=current_user.id,
        action_type="tech_document.update",
        payload={
            "document_id": str(updated_document.id),
            "section_id": str(updated_document.section_id),
            "old_version": old_version,
            "new_version": updated_document.version,
        },
        ip_address=getattr(request.state, "ip", None)
    )

    return TechDocumentUploadResponse.model_validate(updated_document)


@router.delete("/documents/{document_id}")
def delete_document_by_id(
    request: Request,
    document_id: UUID,
    mode: str = Query("soft"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin"]))
):
    if mode not in {"soft", "hard"}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid delete mode")

    document = get_document(db, document_id)
    if not document:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    section = get_section(db, document.section_id)
    success = delete_document(db, document_id, current_user.id, mode)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    notify_tech_document_deleted(db, document, section)

    log_action(
        db,
        user_id=current_user.id,
        action_type="tech_document.delete",
        payload={
            "document_id": str(document.id),
            "section_id": str(document.section_id),
            "mode": mode,
        },
        ip_address=getattr(request.state, "ip", None)
    )

    return {"message": "Document deleted"}


@router.get("/documents/{document_id}/versions", response_model=List[TechDocumentVersionResponse])
def get_document_versions(
    document_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    document = get_document(db, document_id)
    if not document or document.is_deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    versions = list_versions(db, document_id)
    return [TechDocumentVersionResponse.model_validate(v) for v in versions]
