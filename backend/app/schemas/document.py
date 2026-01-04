from datetime import datetime
from uuid import UUID
from typing import Optional, List

from pydantic import BaseModel, Field

from app.schemas.user import UserSummary


class RevisionSummary(BaseModel):
    id: UUID
    revision_label: str
    original_filename: str
    file_size_bytes: int
    is_current: bool
    uploaded_at: datetime

    class Config:
        from_attributes = True


class RevisionResponse(BaseModel):
    id: UUID
    document_id: UUID
    revision_label: str
    original_filename: str
    file_size_bytes: int
    is_current: bool
    change_note: Optional[str]
    author: UserSummary
    uploaded_at: datetime

    class Config:
        from_attributes = True


class DocumentSummary(BaseModel):
    id: UUID
    title: str
    type: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class DocumentResponse(BaseModel):
    id: UUID
    item_id: UUID
    title: str
    type: Optional[str]
    current_revision: Optional[RevisionSummary]
    revisions: List[RevisionSummary] = []
    created_at: datetime
    is_deleted: bool = False
    deleted_at: Optional[datetime] = None
    deleted_by: Optional[UUID] = None

    class Config:
        from_attributes = True


class DocumentCreate(BaseModel):
    item_id: UUID
    title: str = Field(..., max_length=255)
    type: Optional[str] = Field(None, max_length=100)


class RevisionCreate(BaseModel):
    change_note: str

