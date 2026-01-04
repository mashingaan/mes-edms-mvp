from datetime import datetime

from sqlalchemy import Column, BigInteger, String, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID, INET, JSONB

from app.database import Base


class AuditLog(Base):
    __tablename__ = "audit_log"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    action_type = Column(String(100), nullable=False)
    ip_address = Column(INET, nullable=True)
    payload = Column(JSONB, nullable=False)

