import uuid
from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import Column, String, Boolean, Enum, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class UserRole(str, PyEnum):
    admin = "admin"
    responsible = "responsible"
    viewer = "viewer"


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    full_name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), nullable=False, default=UserRole.viewer)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    items = relationship("Item", back_populates="responsible", foreign_keys="Item.responsible_id")
    document_revisions = relationship("DocumentRevision", back_populates="author")
    notifications = relationship("Notification", back_populates="user")
    progress_changes = relationship("ProgressHistory", back_populates="changed_by_user")

