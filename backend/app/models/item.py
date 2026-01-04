import uuid
from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import Column, String, Integer, ForeignKey, Enum, DateTime, CheckConstraint, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class ItemStatus(str, PyEnum):
    draft = "draft"
    in_progress = "in_progress"
    completed = "completed"
    cancelled = "cancelled"


class Item(Base):
    __tablename__ = "items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    section_id = Column(UUID(as_uuid=True), ForeignKey("project_sections.id", ondelete="SET NULL"), nullable=True)
    part_number = Column(String(100), unique=True, nullable=False)
    name = Column(String(255), nullable=False)
    status = Column(Enum(ItemStatus), nullable=False, default=ItemStatus.draft)
    current_progress = Column(Integer, nullable=False, default=0)
    docs_completion_percent = Column(Integer, nullable=True, default=0)
    responsible_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        CheckConstraint("current_progress >= 0 AND current_progress <= 100", name="check_current_progress"),
        CheckConstraint("docs_completion_percent >= 0 AND docs_completion_percent <= 100", name="check_docs_completion_percent"),
        Index("idx_items_section", "section_id"),
    )

    # Relationships
    project = relationship("Project", back_populates="items")
    section = relationship("ProjectSection", back_populates="items")
    responsible = relationship("User", back_populates="items", foreign_keys=[responsible_id])
    documents = relationship("Document", back_populates="item", cascade="all, delete-orphan")
    progress_history = relationship("ProgressHistory", back_populates="item", cascade="all, delete-orphan")

