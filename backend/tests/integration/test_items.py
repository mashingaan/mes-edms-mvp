import pytest
from uuid import uuid4

from app.models.project import Project
from app.models.project_section import ProjectSection
from app.models.audit_log import AuditLog


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
def other_project(db):
    """Create another test project."""
    project = Project(name="Other Project")
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


@pytest.fixture
def other_section(db, other_project):
    """Create section in other project."""
    section = ProjectSection(project_id=other_project.id, code="OTHER-001")
    db.add(section)
    db.commit()
    db.refresh(section)
    return section


def test_create_item_with_docs_completion_percent(client, admin_token, project):
    """Item create accepts docs_completion_percent."""
    response = client.post(
        "/api/items",
        json={
            "project_id": str(project.id),
            "part_number": "DOCS-ITEM-001",
            "name": "Docs Item",
            "docs_completion_percent": 55,
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["docs_completion_percent"] == 55


def test_update_item_docs_completion_percent(client, admin_token, project):
    """Item update persists docs_completion_percent."""
    create_response = client.post(
        "/api/items",
        json={
            "project_id": str(project.id),
            "part_number": "DOCS-ITEM-002",
            "name": "Docs Item Update",
            "docs_completion_percent": 10,
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert create_response.status_code == 200
    item_id = create_response.json()["id"]

    response = client.patch(
        f"/api/items/{item_id}",
        json={"docs_completion_percent": 80},
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["docs_completion_percent"] == 80


def test_create_item_invalid_docs_completion_percent(client, admin_token, project):
    """Docs completion percent out of range is rejected."""
    response = client.post(
        "/api/items",
        json={
            "project_id": str(project.id),
            "part_number": "DOCS-ITEM-003",
            "name": "Docs Item Invalid",
            "docs_completion_percent": 120,
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 422


def test_update_item_section_id(client, admin_token, project, section):
    """Test updating item section_id."""
    # Create item
    create_response = client.post(
        "/api/items",
        json={
            "project_id": str(project.id),
            "part_number": "SEC-ITEM-001",
            "name": "Section Item",
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert create_response.status_code == 200
    item_id = create_response.json()["id"]

    # Update with section_id
    response = client.patch(
        f"/api/items/{item_id}",
        json={"section_id": str(section.id)},
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["section_id"] == str(section.id)


def test_update_item_section_id_invalid(client, admin_token, project):
    """Test updating item with non-existent section_id."""
    # Create item
    create_response = client.post(
        "/api/items",
        json={
            "project_id": str(project.id),
            "part_number": "SEC-ITEM-002",
            "name": "Section Item Invalid",
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert create_response.status_code == 200
    item_id = create_response.json()["id"]

    # Update with non-existent section_id
    fake_section_id = str(uuid4())
    response = client.patch(
        f"/api/items/{item_id}",
        json={"section_id": fake_section_id},
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 400
    assert "not found" in response.json()["detail"].lower()


def test_update_item_section_id_wrong_project(client, admin_token, project, other_section):
    """Test updating item with section from different project."""
    # Create item
    create_response = client.post(
        "/api/items",
        json={
            "project_id": str(project.id),
            "part_number": "SEC-ITEM-003",
            "name": "Section Item Wrong Project",
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert create_response.status_code == 200
    item_id = create_response.json()["id"]

    # Update with section from different project
    response = client.patch(
        f"/api/items/{item_id}",
        json={"section_id": str(other_section.id)},
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 400
    assert "different project" in response.json()["detail"].lower()


def test_update_item_section_id_audit_log(client, admin_token, db, project, section):
    """Test that updating section_id is logged with old/new values."""
    # Create item
    create_response = client.post(
        "/api/items",
        json={
            "project_id": str(project.id),
            "part_number": "SEC-ITEM-004",
            "name": "Section Item Audit",
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert create_response.status_code == 200
    item_id = create_response.json()["id"]

    # Update with section_id
    response = client.patch(
        f"/api/items/{item_id}",
        json={"section_id": str(section.id)},
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 200

    # Check audit log
    audit_log = db.query(AuditLog).filter(
        AuditLog.action_type == "item.update"
    ).order_by(AuditLog.timestamp.desc()).first()

    assert audit_log is not None
    assert "old_values" in audit_log.payload
    assert "new_values" in audit_log.payload
    assert audit_log.payload["old_values"]["section_id"] is None
    assert audit_log.payload["new_values"]["section_id"] == str(section.id)
