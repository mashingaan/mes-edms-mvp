import uuid
from datetime import datetime

from sqlalchemy import Column, String, Integer, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class TechDocumentVersion(Base):
    __tablename__ = "tech_document_versions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey("tech_documents.id", ondelete="CASCADE"), nullable=False)
    version = Column(Integer, nullable=False)
    storage_uuid = Column(UUID(as_uuid=True), nullable=False)
    filename = Column(String(255), nullable=False)
    file_extension = Column(String(10), nullable=False)
    size_bytes = Column(Integer, nullable=False)
    sha256 = Column(String(64), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)

    # Relationships
    document = relationship("TechDocument", back_populates="versions")
    created_by_user = relationship("User", foreign_keys=[created_by])
