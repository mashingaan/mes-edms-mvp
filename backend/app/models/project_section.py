import uuid
from datetime import datetime

from sqlalchemy import Column, String, ForeignKey, DateTime, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class ProjectSection(Base):
    __tablename__ = "project_sections"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    code = Column(String(50), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("project_id", "code", name="uq_project_section_code"),
    )

    # Relationships
    project = relationship("Project", back_populates="sections")
    items = relationship("Item", back_populates="section")

