from datetime import datetime
from uuid import UUID
from typing import Optional, List, TYPE_CHECKING

from pydantic import BaseModel, Field

from app.models.item import ItemStatus
from app.schemas.user import UserSummary
from app.schemas.project import ProjectSectionResponse

if TYPE_CHECKING:
    from app.schemas.document import DocumentSummary


class ItemCreate(BaseModel):
    project_id: UUID
    part_number: str = Field(..., max_length=100)
    name: str = Field(..., max_length=255)
    docs_completion_percent: int = Field(0, ge=0, le=100)
    responsible_id: Optional[UUID] = None
    status: ItemStatus = ItemStatus.draft


class ItemUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    status: Optional[ItemStatus] = None
    docs_completion_percent: Optional[int] = Field(None, ge=0, le=100)
    responsible_id: Optional[UUID] = None
    section_id: Optional[UUID] = None


class ProgressUpdate(BaseModel):
    new_progress: int = Field(..., ge=0, le=100)
    comment: Optional[str] = None


class ItemSummary(BaseModel):
    id: UUID
    part_number: str
    name: str
    status: ItemStatus
    current_progress: int
    section_id: Optional[UUID] = None
    original_filename: Optional[str] = None

    class Config:
        from_attributes = True


class ItemResponse(BaseModel):
    id: UUID
    project_id: UUID
    section_id: Optional[UUID] = None
    section: Optional[ProjectSectionResponse] = None
    part_number: str
    name: str
    status: ItemStatus
    current_progress: int
    docs_completion_percent: Optional[int]
    responsible: Optional[UserSummary]
    documents: List["DocumentSummary"] = []
    created_at: datetime
    original_filename: Optional[str] = None

    class Config:
        from_attributes = True


class ProgressHistoryResponse(BaseModel):
    id: UUID
    item_id: UUID
    old_progress: int
    new_progress: int
    changed_by: UserSummary
    changed_at: datetime
    comment: Optional[str]

    class Config:
        from_attributes = True


class FileImportPreview(BaseModel):
    filename: str
    parsed_section_code: Optional[str]
    parsed_part_number: Optional[str]
    parsed_name: str


class FileImportRequest(BaseModel):
    project_id: UUID
    section_id: Optional[UUID] = None
    responsible_id: Optional[UUID] = None


# Update forward references
from app.schemas.document import DocumentSummary
ItemResponse.model_rebuild()

