from datetime import datetime
from uuid import UUID
from typing import Optional, Any

from pydantic import BaseModel


class NotificationResponse(BaseModel):
    id: UUID
    message: str
    read_at: Optional[datetime]
    created_at: datetime
    event_payload: Optional[dict[str, Any]]

    class Config:
        from_attributes = True

