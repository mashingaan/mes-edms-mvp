from uuid import UUID
from typing import Optional, List

from sqlalchemy.orm import Session

from app.models.document_revision import DocumentRevision


def get_current_revision(db: Session, document_id: UUID) -> Optional[DocumentRevision]:
    """Get current revision for a document."""
    return db.query(DocumentRevision).filter(
        DocumentRevision.document_id == document_id,
        DocumentRevision.is_current == True
    ).first()


def list_revisions(db: Session, document_id: UUID) -> List[DocumentRevision]:
    """List all revisions for a document."""
    return db.query(DocumentRevision).filter(
        DocumentRevision.document_id == document_id
    ).order_by(DocumentRevision.uploaded_at.desc()).all()

