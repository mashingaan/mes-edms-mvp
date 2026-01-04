from datetime import datetime
from uuid import UUID
from typing import Optional, List, TYPE_CHECKING

from pydantic import BaseModel, Field

from app.models.project import ProjectStatus

if TYPE_CHECKING:
    from app.schemas.item import ItemSummary


class ProjectSectionCreate(BaseModel):
    project_id: UUID
    code: str = Field(..., max_length=50)


class ProjectSectionResponse(BaseModel):
    id: UUID
    project_id: UUID
    code: str
    created_at: datetime

    class Config:
        from_attributes = True


class ProjectCreate(BaseModel):
    name: str = Field(..., max_length=255)
    description: Optional[str] = None
    status: ProjectStatus = ProjectStatus.active


class ProjectUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    status: Optional[ProjectStatus] = None


class ProjectResponse(BaseModel):
    id: UUID
    name: str
    status: ProjectStatus
    description: Optional[str]
    created_at: datetime
    items: List["ItemSummary"] = []
    sections: List[ProjectSectionResponse] = []

    class Config:
        from_attributes = True


class ProjectSummary(BaseModel):
    id: UUID
    name: str
    status: ProjectStatus

    class Config:
        from_attributes = True


# Update forward references
from app.schemas.item import ItemSummary
ProjectResponse.model_rebuild()

