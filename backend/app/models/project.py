import uuid
from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import Column, String, Text, Enum, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class ProjectStatus(str, PyEnum):
    active = "active"
    archived = "archived"
    on_hold = "on_hold"


class Project(Base):
    __tablename__ = "projects"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    status = Column(Enum(ProjectStatus), nullable=False, default=ProjectStatus.active)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    items = relationship("Item", back_populates="project", cascade="all, delete-orphan")
    sections = relationship("ProjectSection", back_populates="project", cascade="all, delete-orphan")

