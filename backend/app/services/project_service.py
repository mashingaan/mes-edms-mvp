from uuid import UUID
from typing import Optional, List

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.models.project import Project
from app.models.project_section import ProjectSection
from app.schemas.project import ProjectCreate, ProjectUpdate


def create_project(db: Session, project_data: ProjectCreate) -> Project:
    """Create a new project."""
    project = Project(
        name=project_data.name,
        description=project_data.description,
        status=project_data.status,
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


def get_project(db: Session, project_id: UUID) -> Optional[Project]:
    """Get project by ID."""
    return db.query(Project).filter(Project.id == project_id).first()


def list_projects(db: Session) -> List[Project]:
    """List all projects."""
    return db.query(Project).all()


def update_project(db: Session, project_id: UUID, project_data: ProjectUpdate) -> Optional[Project]:
    """Update project."""
    project = get_project(db, project_id)
    if not project:
        return None
    
    update_data = project_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(project, field, value)
    
    db.commit()
    db.refresh(project)
    return project


def delete_project(db: Session, project_id: UUID) -> bool:
    """Delete project."""
    project = get_project(db, project_id)
    if not project:
        return False
    
    db.delete(project)
    db.commit()
    return True


def create_section(db: Session, project_id: UUID, code: str, commit: bool = True) -> ProjectSection:
    """Create a new section in project or return existing if already exists.
    
    Args:
        db: Database session
        project_id: Project UUID
        code: Section code
        commit: If True, commit transaction. If False, only flush (for batch operations).
    """
    existing = db.query(ProjectSection).filter(
        ProjectSection.project_id == project_id,
        ProjectSection.code == code
    ).first()
    
    if existing:
        return existing
    
    section = ProjectSection(
        project_id=project_id,
        code=code,
    )
    
    try:
        db.add(section)
        if commit:
            db.commit()
            db.refresh(section)
        else:
            db.flush()  # Get section.id without committing
        return section
    except IntegrityError:
        if commit:
            db.rollback()
        # Handle race condition - return existing section
        return db.query(ProjectSection).filter(
            ProjectSection.project_id == project_id,
            ProjectSection.code == code
        ).first()


def list_sections(db: Session, project_id: UUID) -> List[ProjectSection]:
    """List all sections for a project."""
    return db.query(ProjectSection).filter(
        ProjectSection.project_id == project_id
    ).all()


def get_or_create_section(db: Session, project_id: UUID, code: str, commit: bool = True) -> ProjectSection:
    """Get existing section or create new one (helper for import).
    
    Args:
        db: Database session
        project_id: Project UUID
        code: Section code
        commit: If True, commit transaction. If False, only flush (for batch operations).
    """
    return create_section(db, project_id, code, commit=commit)

