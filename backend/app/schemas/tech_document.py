from datetime import datetime
from uuid import UUID
from typing import List

from pydantic import BaseModel

from app.schemas.user import UserSummary


class TechDocumentResponse(BaseModel):
    id: UUID
    section_id: UUID
    filename: str
    size_bytes: int
    version: int
    created_at: datetime
    created_by_user: UserSummary

    class Config:
        from_attributes = True


class TechDocumentUploadResponse(BaseModel):
    id: UUID
    filename: str
    version: int

    class Config:
        from_attributes = True


class TechDocumentVersionResponse(BaseModel):
    id: UUID
    version: int
    filename: str
    created_at: datetime
    created_by_user: UserSummary

    class Config:
        from_attributes = True


class SheetPreview(BaseModel):
    name: str
    rows: List[List[str]]
    total_rows: int

    class Config:
        from_attributes = True


class TechDocumentPreviewResponse(BaseModel):
    filename: str
    sheets: List[SheetPreview]

    class Config:
        from_attributes = True
