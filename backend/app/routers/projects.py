from uuid import UUID
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.project import ProjectCreate, ProjectUpdate, ProjectResponse, ProjectSectionResponse
from app.services.project_service import (
    create_project,
    get_project,
    list_projects,
    update_project,
    delete_project,
    create_section,
    list_sections,
)
from app.services.audit_service import log_action
from app.dependencies import get_current_user, require_role
from app.models.user import User

router = APIRouter()


class SectionCreateRequest(BaseModel):
    code: str = Field(..., max_length=50)


@router.get("", response_model=List[ProjectResponse])
async def get_projects(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    projects = list_projects(db)
    return [ProjectResponse.model_validate(p) for p in projects]


@router.post("", response_model=ProjectResponse)
async def create_new_project(
    request: Request,
    project_data: ProjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin"]))
):
    project = create_project(db, project_data)
    
    # Audit log
    log_action(
        db,
        user_id=current_user.id,
        action_type="project.create",
        payload={"project_id": str(project.id), "name": project.name},
        ip_address=getattr(request.state, "ip", None)
    )
    
    return ProjectResponse.model_validate(project)


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project_by_id(
    project_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    project = get_project(db, project_id)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    return ProjectResponse.model_validate(project)


@router.patch("/{project_id}", response_model=ProjectResponse)
async def update_project_by_id(
    request: Request,
    project_id: UUID,
    project_data: ProjectUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin"]))
):
    # Get project before update to capture old values
    project = get_project(db, project_id)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    
    # Save old values before update
    changes = project_data.model_dump(exclude_unset=True)
    old_values = {field: getattr(project, field) for field in changes.keys()}
    
    # Update project
    updated_project = update_project(db, project_id, project_data)
    
    # Get new values after update
    new_values = changes.copy()
    
    # Audit log with old/new values
    log_action(
        db,
        user_id=current_user.id,
        action_type="project.update",
        payload={
            "project_id": str(project_id),
            "changes": jsonable_encoder(changes),
            "old_values": jsonable_encoder(old_values),
            "new_values": jsonable_encoder(new_values)
        },
        ip_address=getattr(request.state, "ip", None)
    )
    
    return ProjectResponse.model_validate(updated_project)


@router.delete("/{project_id}")
async def delete_project_by_id(
    request: Request,
    project_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin"]))
):
    success = delete_project(db, project_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    
    # Audit log
    log_action(
        db,
        user_id=current_user.id,
        action_type="project.delete",
        payload={"project_id": str(project_id)},
        ip_address=getattr(request.state, "ip", None)
    )
    
    return {"message": "Project deleted"}


@router.post("/{project_id}/sections", response_model=ProjectSectionResponse)
async def create_project_section(
    request: Request,
    project_id: UUID,
    section_data: SectionCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin"]))
):
    """Create a new section in project (or return existing if already exists)."""
    project = get_project(db, project_id)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    
    section = create_section(db, project_id, section_data.code)
    
    # Audit log
    log_action(
        db,
        user_id=current_user.id,
        action_type="project.section_create",
        payload={"project_id": str(project_id), "section_id": str(section.id), "code": section.code},
        ip_address=getattr(request.state, "ip", None)
    )
    
    return ProjectSectionResponse.model_validate(section)


@router.get("/{project_id}/sections", response_model=List[ProjectSectionResponse])
async def get_project_sections(
    project_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all sections for a project."""
    project = get_project(db, project_id)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    
    sections = list_sections(db, project_id)
    return [ProjectSectionResponse.model_validate(s) for s in sections]

