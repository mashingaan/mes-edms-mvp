import pytest
import io

from app.models.project import Project
from app.models.item import Item


@pytest.fixture
def project(db):
    """Create test project."""
    project = Project(name="Test Project")
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


@pytest.fixture
def item_for_responsible(db, project, responsible_user):
    """Create test item assigned to responsible user."""
    item = Item(
        project_id=project.id,
        part_number="TEST-RBAC-001",
        name="Test Item",
        responsible_id=responsible_user.id,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@pytest.fixture
def item_for_other(db, project, admin_user):
    """Create test item assigned to admin."""
    item = Item(
        project_id=project.id,
        part_number="TEST-RBAC-002",
        name="Admin Item",
        responsible_id=admin_user.id,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def test_admin_can_create_user(client, admin_token):
    """Admin can create user."""
    response = client.post(
        "/api/users",
        json={
            "full_name": "New User",
            "email": "newuser@test.com",
            "password": "password123",
            "role": "viewer"
        },
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    assert response.status_code == 200
    assert response.json()["email"] == "newuser@test.com"


def test_responsible_cannot_create_user(client, responsible_token):
    """Responsible user cannot create user."""
    response = client.post(
        "/api/users",
        json={
            "full_name": "New User",
            "email": "newuser2@test.com",
            "password": "password123",
            "role": "viewer"
        },
        headers={"Authorization": f"Bearer {responsible_token}"}
    )
    
    assert response.status_code == 403


def test_viewer_cannot_create_user(client, viewer_token):
    """Viewer cannot create user."""
    response = client.post(
        "/api/users",
        json={
            "full_name": "New User",
            "email": "newuser3@test.com",
            "password": "password123",
            "role": "viewer"
        },
        headers={"Authorization": f"Bearer {viewer_token}"}
    )
    
    assert response.status_code == 403


def test_viewer_cannot_upload_document(client, viewer_token, item_for_responsible):
    """Viewer cannot upload document."""
    pdf_content = b"%PDF-1.4 test content"
    files = {"file": ("test.pdf", io.BytesIO(pdf_content), "application/pdf")}
    data = {
        "item_id": str(item_for_responsible.id),
        "title": "Test Document",
    }
    
    response = client.post(
        "/api/documents",
        files=files,
        data=data,
        headers={"Authorization": f"Bearer {viewer_token}"}
    )
    
    assert response.status_code == 403


def test_responsible_can_upload_for_assigned_item(client, responsible_token, item_for_responsible):
    """Responsible user can upload for assigned item."""
    pdf_content = b"%PDF-1.4 test content"
    files = {"file": ("test.pdf", io.BytesIO(pdf_content), "application/pdf")}
    data = {
        "item_id": str(item_for_responsible.id),
        "title": "Test Document",
    }
    
    response = client.post(
        "/api/documents",
        files=files,
        data=data,
        headers={"Authorization": f"Bearer {responsible_token}"}
    )
    
    assert response.status_code == 200


def test_responsible_cannot_upload_for_other_item(client, responsible_token, item_for_other):
    """Responsible user cannot upload for other's item."""
    pdf_content = b"%PDF-1.4 test content"
    files = {"file": ("test.pdf", io.BytesIO(pdf_content), "application/pdf")}
    data = {
        "item_id": str(item_for_other.id),
        "title": "Test Document",
    }
    
    response = client.post(
        "/api/documents",
        files=files,
        data=data,
        headers={"Authorization": f"Bearer {responsible_token}"}
    )
    
    assert response.status_code == 403


def test_admin_can_view_audit_log(client, admin_token):
    """Admin can view audit log."""
    response = client.get(
        "/api/audit",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    assert response.status_code == 200


def test_viewer_cannot_view_audit_log(client, viewer_token):
    """Viewer cannot view audit log."""
    response = client.get(
        "/api/audit",
        headers={"Authorization": f"Bearer {viewer_token}"}
    )
    
    assert response.status_code == 403


def test_responsible_cannot_view_audit_log(client, responsible_token):
    """Responsible user cannot view audit log."""
    response = client.get(
        "/api/audit",
        headers={"Authorization": f"Bearer {responsible_token}"}
    )
    
    assert response.status_code == 403

