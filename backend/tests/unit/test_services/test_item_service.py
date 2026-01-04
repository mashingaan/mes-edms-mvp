import pytest
from uuid import uuid4

from app.models.project import Project
from app.models.project_section import ProjectSection
from app.models.item import Item, ItemStatus
from app.schemas.item import ItemCreate, ItemUpdate
from app.services.item_service import create_item, get_item, update_item


@pytest.fixture
def project(db):
    """Create test project."""
    project = Project(name="Test Project")
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


@pytest.fixture
def section(db, project):
    """Create test section."""
    section = ProjectSection(project_id=project.id, code="SEC-001")
    db.add(section)
    db.commit()
    db.refresh(section)
    return section


@pytest.fixture
def item(db, project):
    """Create test item."""
    item = Item(
        project_id=project.id,
        part_number="ITEM-001",
        name="Test Item",
        status=ItemStatus.draft,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def test_update_item_with_section_id(db, item, section):
    """Test updating item with section_id."""
    item_data = ItemUpdate(section_id=section.id)
    
    updated_item = update_item(db, item.id, item_data)
    
    assert updated_item is not None
    assert updated_item.section_id == section.id


def test_update_item_with_section_id_to_none(db, project, section):
    """Test updating item section_id to None."""
    # Create item with section
    item = Item(
        project_id=project.id,
        part_number="ITEM-002",
        name="Test Item With Section",
        section_id=section.id,
        status=ItemStatus.draft,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    
    # Update section_id to None
    item_data = ItemUpdate(section_id=None)
    
    updated_item = update_item(db, item.id, item_data)
    
    assert updated_item is not None
    assert updated_item.section_id is None


def test_update_item_returns_updated_entity(db, item):
    """Test that update_item returns the updated entity."""
    new_name = "Updated Item Name"
    item_data = ItemUpdate(name=new_name, status=ItemStatus.in_progress)
    
    updated_item = update_item(db, item.id, item_data)
    
    assert updated_item is not None
    assert updated_item.name == new_name
    assert updated_item.status == ItemStatus.in_progress


def test_update_item_not_found(db):
    """Test updating non-existent item returns None."""
    fake_id = uuid4()
    item_data = ItemUpdate(name="New Name")
    
    result = update_item(db, fake_id, item_data)
    
    assert result is None

