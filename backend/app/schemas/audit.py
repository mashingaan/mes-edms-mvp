from datetime import datetime
from uuid import UUID
from typing import Optional, Any

from pydantic import BaseModel

from app.schemas.user import UserSummary


class AuditLogResponse(BaseModel):
    id: int
    timestamp: datetime
    user: Optional[UserSummary]
    action_type: str
    ip_address: Optional[str]
    payload: dict[str, Any]

    class Config:
        from_attributes = True

