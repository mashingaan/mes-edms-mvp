import uuid
from datetime import datetime

from sqlalchemy import Column, String, ForeignKey, DateTime, Boolean, and_
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class Document(Base):
    __tablename__ = "documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    item_id = Column(UUID(as_uuid=True), ForeignKey("items.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(255), nullable=False)
    type = Column(String(100), nullable=True)  # e.g., "Чертеж", "Спецификация"
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_deleted = Column(Boolean, nullable=False, default=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    deleted_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    # Relationships
    deleted_by_user = relationship("User", foreign_keys=[deleted_by])
    item = relationship("Item", back_populates="documents")
    revisions = relationship("DocumentRevision", back_populates="document", cascade="all, delete-orphan")
    current_revision = relationship(
        "DocumentRevision",
        primaryjoin="and_(Document.id == foreign(DocumentRevision.document_id), DocumentRevision.is_current == True)",
        uselist=False,
        viewonly=True,
        lazy="selectin"
    )

