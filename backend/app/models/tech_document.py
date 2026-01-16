import uuid
from datetime import datetime

from sqlalchemy import Column, String, ForeignKey, DateTime, Boolean, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class TechDocument(Base):
    __tablename__ = "tech_documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    section_id = Column(UUID(as_uuid=True), ForeignKey("project_sections.id", ondelete="CASCADE"), nullable=False)
    filename = Column(String(255), nullable=False)
    storage_uuid = Column(UUID(as_uuid=True), nullable=False)
    file_extension = Column(String(10), nullable=False)
    size_bytes = Column(Integer, nullable=False)
    sha256 = Column(String(64), nullable=False)
    version = Column(Integer, nullable=False, default=1)
    is_current = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    is_deleted = Column(Boolean, nullable=False, default=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    deleted_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    # Relationships
    section = relationship("ProjectSection")
    created_by_user = relationship("User", foreign_keys=[created_by])
    deleted_by_user = relationship("User", foreign_keys=[deleted_by])
    versions = relationship("TechDocumentVersion", back_populates="document", cascade="all, delete-orphan")
