import uuid
from datetime import datetime

from sqlalchemy import Column, String, BigInteger, Boolean, Text, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class DocumentRevision(Base):
    __tablename__ = "document_revisions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    revision_label = Column(String(10), nullable=False)
    file_storage_uuid = Column(UUID(as_uuid=True), nullable=False, unique=True)
    original_filename = Column(String(255), nullable=False)
    mime_type = Column(String(100), nullable=False)
    file_size_bytes = Column(BigInteger, nullable=False)
    sha256_hash = Column(String(64), nullable=False)
    is_current = Column(Boolean, nullable=False, default=False)
    change_note = Column(Text, nullable=True)
    author_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    uploaded_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    # Relationships
    document = relationship("Document", back_populates="revisions")
    author = relationship("User", back_populates="document_revisions")

