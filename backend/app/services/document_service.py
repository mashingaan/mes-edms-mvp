import logging
import uuid
from uuid import UUID
from typing import Optional, List, Tuple
from pathlib import Path
from datetime import datetime

from sqlalchemy.orm import Session, selectinload
from fastapi import UploadFile, HTTPException, status

from app.models.document import Document
from app.models.document_revision import DocumentRevision
from app.services.file_storage_service import save_file, get_file_path
from app.services.revision_service import get_current_revision
from app.services.notification_service import notify_revision_uploaded
from app.utils.revision_helper import get_next_revision
from app.utils.validators import validate_pdf_header


logger = logging.getLogger(__name__)


async def create_document(
    db: Session,
    item_id: UUID,
    title: str,
    type: Optional[str],
    file: UploadFile,
    author_id: UUID
) -> Document:
    """Create a new document with initial revision '-'."""
    # Validate PDF
    await validate_pdf_header(file)
    
    # Create document
    document = Document(
        item_id=item_id,
        title=title,
        type=type,
    )
    db.add(document)
    db.flush()  # Get document ID
    
    # Save file and create initial revision
    file_info = await save_file(file)
    
    revision = DocumentRevision(
        document_id=document.id,
        revision_label="-",
        file_storage_uuid=file_info["uuid"],
        original_filename=file.filename,
        mime_type="application/pdf",
        file_size_bytes=file_info["size_bytes"],
        sha256_hash=file_info["sha256"],
        is_current=True,
        author_id=author_id,
    )
    db.add(revision)
    
    db.commit()
    db.refresh(document)
    db.refresh(revision)
    
    # Notify responsible user and admins about new revision
    notify_revision_uploaded(db, document, revision)
    
    return document


def get_document(db: Session, document_id: UUID) -> Optional[Document]:
    """Get document by ID with revisions eagerly loaded."""
    return db.query(Document).options(
        selectinload(Document.revisions),
        selectinload(Document.current_revision)
    ).filter(Document.id == document_id).first()


def list_documents(db: Session, item_id: Optional[UUID] = None, show_deleted: bool = False) -> List[Document]:
    """List documents, optionally filtered by item, with revisions eagerly loaded."""
    query = db.query(Document).options(
        selectinload(Document.revisions),
        selectinload(Document.current_revision)
    )
    if not show_deleted:
        query = query.filter(Document.is_deleted == False)
    if item_id:
        query = query.filter(Document.item_id == item_id)
    return query.all()


async def upload_revision(
    db: Session,
    document_id: UUID,
    file: UploadFile,
    change_note: str,
    author_id: UUID
) -> DocumentRevision:
    """Upload a new revision for a document."""
    document = get_document(db, document_id)
    if not document or document.is_deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )

    # Validate PDF
    await validate_pdf_header(file)
    
    # Get current revision with lock
    current_rev = db.query(DocumentRevision).filter(
        DocumentRevision.document_id == document_id,
        DocumentRevision.is_current == True
    ).with_for_update().first()
    
    if not current_rev:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No current revision found"
        )
    
    # Validate change_note required for revisions after initial
    if current_rev.revision_label != "-" and not change_note:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Change note is required for revisions after initial upload"
        )
    
    # Save file
    file_info = await save_file(file)

    try:
        # Calculate next revision label
        next_label = get_next_revision(current_rev.revision_label)
    except ValueError as exc:
        db.rollback()
        from app.services.file_storage_service import delete_file
        delete_file(file_info["uuid"])
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc) or "Invalid revision label"
        )
    
    try:
        # Mark current as not current
        current_rev.is_current = False
        
        # Create new revision
        new_revision = DocumentRevision(
            document_id=document_id,
            revision_label=next_label,
            file_storage_uuid=file_info["uuid"],
            original_filename=file.filename,
            mime_type="application/pdf",
            file_size_bytes=file_info["size_bytes"],
            sha256_hash=file_info["sha256"],
            is_current=True,
            change_note=change_note,
            author_id=author_id,
        )
        db.add(new_revision)
        
        db.commit()
        db.refresh(new_revision)
        
        # Notify responsible user and admins about new revision
        document = get_document(db, document_id)
        notify_revision_uploaded(db, document, new_revision)
        
        return new_revision
    except Exception as e:
        # Rollback and delete file on error
        db.rollback()
        from app.services.file_storage_service import delete_file
        delete_file(file_info["uuid"])
        raise e


def soft_delete_document(db: Session, document_id: UUID, user_id: UUID) -> Optional[Document]:
    """Soft delete document by marking it as deleted."""
    document = get_document(db, document_id)
    if not document:
        return None
    
    # Idempotent: if already deleted, just return
    if document.is_deleted:
        return document
    
    document.is_deleted = True
    document.deleted_at = datetime.utcnow()
    document.deleted_by = user_id
    
    db.commit()
    db.refresh(document)
    return document


def hard_delete_document(db: Session, document_id: UUID) -> bool:
    """Hard delete document and all its files."""
    from app.services.file_storage_service import delete_file
    
    document = get_document(db, document_id)
    if not document:
        return False
    
    # Delete all revision files
    for revision in document.revisions:
        delete_file(revision.file_storage_uuid)
    
    db.delete(document)
    db.commit()
    return True


def get_revision_file_path(
    db: Session,
    document_id: UUID,
    revision_id: UUID
) -> Optional[Tuple[Path, str]]:
    """Get file path and download filename for a revision."""
    revision = db.query(DocumentRevision).filter(
        DocumentRevision.id == revision_id,
        DocumentRevision.document_id == document_id
    ).first()
    
    if not revision:
        return None
    
    # Get document and item for filename
    document = get_document(db, document_id)
    if not document or document.is_deleted:
        return None
    from app.services.item_service import get_item
    item = get_item(db, document.item_id)
    
    # Build download filename: {part_number}_{revision}.pdf
    filename = f"{item.part_number}_{revision.revision_label}.pdf"
    
    path = get_file_path(revision.file_storage_uuid)
    if not path.exists():
        logger.warning(
            "Revision file missing on disk",
            extra={
                "document_id": str(document_id),
                "revision_id": str(revision_id),
                "path": str(path),
            },
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Revision file not found",
        )
    return (path, filename)

