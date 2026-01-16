from datetime import datetime
from typing import List, Optional
from uuid import UUID

from fastapi import UploadFile, HTTPException, status
from sqlalchemy.orm import Session, selectinload

from app.models.tech_document import TechDocument
from app.models.tech_document_version import TechDocumentVersion
from app.services.file_storage_service import save_excel_file, delete_excel_file


def list_documents(db: Session, section_id: UUID) -> List[TechDocument]:
    """List current tech documents for a section."""
    return db.query(TechDocument).options(
        selectinload(TechDocument.created_by_user)
    ).filter(
        TechDocument.section_id == section_id,
        TechDocument.is_deleted == False,
        TechDocument.is_current == True
    ).all()


async def upload_document(
    db: Session,
    section_id: UUID,
    file: UploadFile,
    user_id: UUID
) -> TechDocument:
    """Upload a new tech document."""
    file_info = await save_excel_file(file)

    try:
        document = TechDocument(
            section_id=section_id,
            filename=file.filename or "unnamed.xlsx",
            storage_uuid=file_info["uuid"],
            file_extension=file_info["extension"],
            size_bytes=file_info["size_bytes"],
            sha256=file_info["sha256"],
            version=1,
            is_current=True,
            created_by=user_id,
        )
        db.add(document)
        db.commit()
        db.refresh(document)
        return document
    except Exception:
        db.rollback()
        delete_excel_file(file_info["uuid"], file_info["extension"])
        raise


def get_document(db: Session, document_id: UUID) -> Optional[TechDocument]:
    """Get tech document by ID."""
    return db.query(TechDocument).options(
        selectinload(TechDocument.created_by_user)
    ).filter(TechDocument.id == document_id).first()


async def update_document(
    db: Session,
    document_id: UUID,
    file: UploadFile,
    user_id: UUID
) -> TechDocument:
    """Upload a new version for a tech document."""
    document = get_document(db, document_id)
    if not document or document.is_deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )

    version_entry = TechDocumentVersion(
        document_id=document.id,
        version=document.version,
        storage_uuid=document.storage_uuid,
        filename=document.filename,
        file_extension=document.file_extension,
        size_bytes=document.size_bytes,
        sha256=document.sha256,
        created_by=user_id,
    )
    db.add(version_entry)

    document.is_current = False

    file_info = None
    try:
        file_info = await save_excel_file(file)
        document.storage_uuid = file_info["uuid"]
        document.filename = file.filename or document.filename
        document.file_extension = file_info["extension"]
        document.size_bytes = file_info["size_bytes"]
        document.sha256 = file_info["sha256"]
        document.version = document.version + 1
        document.is_current = True

        db.commit()
        db.refresh(document)
        return document
    except Exception:
        db.rollback()
        if file_info:
            delete_excel_file(file_info["uuid"], file_info["extension"])
        raise


def delete_document(db: Session, document_id: UUID, user_id: UUID, mode: str) -> bool:
    """Delete tech document (soft delete by default)."""
    document = get_document(db, document_id)
    if not document:
        return False

    if mode == "hard":
        delete_excel_file(document.storage_uuid, document.file_extension)
        db.delete(document)
        db.commit()
        return True

    if document.is_deleted:
        return True

    document.is_deleted = True
    document.deleted_at = datetime.utcnow()
    document.deleted_by = user_id
    db.commit()
    return True


def list_versions(db: Session, document_id: UUID) -> List[TechDocumentVersion]:
    """List tech document versions."""
    return db.query(TechDocumentVersion).options(
        selectinload(TechDocumentVersion.created_by_user)
    ).filter(TechDocumentVersion.document_id == document_id).order_by(
        TechDocumentVersion.version.desc()
    ).all()
