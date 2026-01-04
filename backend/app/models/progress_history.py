import uuid
from datetime import datetime

from sqlalchemy import Column, Integer, Text, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class ProgressHistory(Base):
    __tablename__ = "progress_history"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    item_id = Column(UUID(as_uuid=True), ForeignKey("items.id", ondelete="CASCADE"), nullable=False)
    old_progress = Column(Integer, nullable=False)
    new_progress = Column(Integer, nullable=False)
    changed_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    changed_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    comment = Column(Text, nullable=True)

    # Relationships
    item = relationship("Item", back_populates="progress_history")
    changed_by_user = relationship("User", back_populates="progress_changes")

