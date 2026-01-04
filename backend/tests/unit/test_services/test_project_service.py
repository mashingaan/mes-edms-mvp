import pytest
from uuid import uuid4

from app.models.project import Project, ProjectStatus
from app.schemas.project import ProjectCreate, ProjectUpdate
from app.services.project_service import create_project, get_project, update_project


@pytest.fixture
def project(db):
    """Create test project."""
    project = Project(
        name="Test Project",
        description="Test Description",
        status=ProjectStatus.active,
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


def test_update_project_returns_updated_entity(db, project):
    """Test that update_project returns the updated entity."""
    new_name = "Updated Project Name"
    new_status = ProjectStatus.on_hold
    project_data = ProjectUpdate(name=new_name, status=new_status)
    
    updated_project = update_project(db, project.id, project_data)
    
    assert updated_project is not None
    assert updated_project.name == new_name
    assert updated_project.status == new_status


def test_update_project_partial_update(db, project):
    """Test partial update of project."""
    original_description = project.description
    new_name = "Partially Updated Name"
    project_data = ProjectUpdate(name=new_name)
    
    updated_project = update_project(db, project.id, project_data)
    
    assert updated_project is not None
    assert updated_project.name == new_name
    # Description should remain unchanged
    assert updated_project.description == original_description


def test_update_project_not_found(db):
    """Test updating non-existent project returns None."""
    fake_id = uuid4()
    project_data = ProjectUpdate(name="New Name")
    
    result = update_project(db, fake_id, project_data)
    
    assert result is None


def test_update_project_all_fields(db, project):
    """Test updating all fields of project."""
    project_data = ProjectUpdate(
        name="Fully Updated",
        description="New Description",
        status=ProjectStatus.archived,
    )
    
    updated_project = update_project(db, project.id, project_data)
    
    assert updated_project is not None
    assert updated_project.name == "Fully Updated"
    assert updated_project.description == "New Description"
    assert updated_project.status == ProjectStatus.archived

