import pytest
import io

from app.models.project import Project
from app.models.item import Item
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
def item(db, project, responsible_user):
    """Create test item."""
    item = Item(
        project_id=project.id,
        part_number="TEST-AUDIT-001",
        name="Test Item",
        responsible_id=responsible_user.id,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def test_audit_log_on_user_create(client, admin_token, db):
    """Audit log is created when user is created."""
    # Clear existing audit logs
    db.query(AuditLog).delete()
    db.commit()
    
    response = client.post(
        "/api/users",
        json={
            "full_name": "New User",
            "email": "newuser_audit@test.com",
            "password": "password123",
            "role": "viewer"
        },
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    assert response.status_code == 200
    
    # Check audit log was created
    audit_logs = db.query(AuditLog).filter(
        AuditLog.action_type == "user.create"
    ).all()
    
    assert len(audit_logs) >= 1
    assert audit_logs[0].payload.get("email") == "newuser_audit@test.com"


def test_audit_log_on_user_update(client, admin_token, db, viewer_user):
    """Audit log is created when user is updated."""
    # Clear existing audit logs
    db.query(AuditLog).delete()
    db.commit()
    
    response = client.patch(
        f"/api/users/{viewer_user.id}",
        json={"full_name": "Updated Viewer Name"},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    assert response.status_code == 200
    
    # Check audit log was created
    audit_logs = db.query(AuditLog).filter(
        AuditLog.action_type == "user.update"
    ).all()
    
    assert len(audit_logs) >= 1
    assert audit_logs[0].payload.get("updated_user_id") == str(viewer_user.id)


def test_audit_log_on_user_delete(client, admin_token, db, viewer_user):
    """Audit log is created when user is deleted (deactivated)."""
    # Clear existing audit logs
    db.query(AuditLog).delete()
    db.commit()
    
    response = client.delete(
        f"/api/users/{viewer_user.id}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    assert response.status_code == 200
    
    # Check audit log was created
    audit_logs = db.query(AuditLog).filter(
        AuditLog.action_type == "user.delete"
    ).all()
    
    assert len(audit_logs) >= 1
    assert audit_logs[0].payload.get("deleted_user_id") == str(viewer_user.id)


def test_audit_log_on_project_create(client, admin_token, db):
    """Audit log is created when project is created."""
    # Clear existing audit logs
    db.query(AuditLog).delete()
    db.commit()
    
    response = client.post(
        "/api/projects",
        json={"name": "Audit Test Project"},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    assert response.status_code == 200
    
    # Check audit log was created
    audit_logs = db.query(AuditLog).filter(
        AuditLog.action_type == "project.create"
    ).all()
    
    assert len(audit_logs) >= 1
    assert audit_logs[0].payload.get("name") == "Audit Test Project"


def test_audit_log_on_project_update(client, admin_token, db, project):
    """Audit log is created when project is updated."""
    # Clear existing audit logs
    db.query(AuditLog).delete()
    db.commit()
    
    response = client.patch(
        f"/api/projects/{project.id}",
        json={"name": "Updated Project Name"},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    assert response.status_code == 200
    
    # Check audit log was created
    audit_logs = db.query(AuditLog).filter(
        AuditLog.action_type == "project.update"
    ).all()
    
    assert len(audit_logs) >= 1
    assert audit_logs[0].payload.get("project_id") == str(project.id)


def test_audit_log_on_project_delete(client, admin_token, db, project):
    """Audit log is created when project is deleted."""
    project_id = project.id
    
    # Clear existing audit logs
    db.query(AuditLog).delete()
    db.commit()
    
    response = client.delete(
        f"/api/projects/{project_id}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    assert response.status_code == 200
    
    # Check audit log was created
    audit_logs = db.query(AuditLog).filter(
        AuditLog.action_type == "project.delete"
    ).all()
    
    assert len(audit_logs) >= 1
    assert audit_logs[0].payload.get("project_id") == str(project_id)


def test_audit_log_on_item_create(client, admin_token, db, project):
    """Audit log is created when item is created."""
    # Clear existing audit logs
    db.query(AuditLog).delete()
    db.commit()
    
    response = client.post(
        "/api/items",
        json={
            "project_id": str(project.id),
            "part_number": "AUDIT-ITEM-001",
            "name": "Audit Test Item"
        },
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    assert response.status_code == 200
    
    # Check audit log was created
    audit_logs = db.query(AuditLog).filter(
        AuditLog.action_type == "item.create"
    ).all()
    
    assert len(audit_logs) >= 1
    assert audit_logs[0].payload.get("part_number") == "AUDIT-ITEM-001"


def test_audit_log_on_item_progress_update(client, admin_token, db, item):
    """Audit log is created when item progress is updated."""
    # Clear existing audit logs
    db.query(AuditLog).delete()
    db.commit()
    
    response = client.patch(
        f"/api/items/{item.id}/progress",
        json={"new_progress": 50, "comment": "Audit test"},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    assert response.status_code == 200
    
    # Check audit log was created
    audit_logs = db.query(AuditLog).filter(
        AuditLog.action_type == "item.progress_update"
    ).all()
    
    assert len(audit_logs) >= 1
    assert audit_logs[0].payload.get("new_progress") == 50
    assert audit_logs[0].payload.get("old_progress") == 0


def test_audit_log_on_document_create(client, admin_token, db, item):
    """Audit log is created when document is created."""
    # Clear existing audit logs
    db.query(AuditLog).delete()
    db.commit()
    
    pdf_content = b"%PDF-1.4 test content"
    files = {"file": ("audit_test.pdf", io.BytesIO(pdf_content), "application/pdf")}
    data = {
        "item_id": str(item.id),
        "title": "Audit Test Document",
    }
    
    response = client.post(
        "/api/documents",
        files=files,
        data=data,
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    assert response.status_code == 200
    
    # Check audit log was created
    audit_logs = db.query(AuditLog).filter(
        AuditLog.action_type == "document.create"
    ).all()
    
    assert len(audit_logs) >= 1
    assert audit_logs[0].payload.get("title") == "Audit Test Document"


def test_audit_log_on_revision_upload(client, admin_token, db, item):
    """Audit log is created when new revision is uploaded."""
    # First create a document
    pdf_content = b"%PDF-1.4 test content"
    files = {"file": ("test.pdf", io.BytesIO(pdf_content), "application/pdf")}
    data = {
        "item_id": str(item.id),
        "title": "Test Document",
    }
    
    response = client.post(
        "/api/documents",
        files=files,
        data=data,
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    doc_id = response.json()["id"]
    
    # Clear existing audit logs
    db.query(AuditLog).delete()
    db.commit()
    
    # Upload new revision
    pdf_content2 = b"%PDF-1.4 updated content"
    files2 = {"file": ("test_v2.pdf", io.BytesIO(pdf_content2), "application/pdf")}
    data2 = {"change_note": "Audit test revision"}
    
    response2 = client.post(
        f"/api/documents/{doc_id}/revisions",
        files=files2,
        data=data2,
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    assert response2.status_code == 200
    
    # Check audit log was created
    audit_logs = db.query(AuditLog).filter(
        AuditLog.action_type == "document.revision_upload"
    ).all()
    
    assert len(audit_logs) >= 1
    assert audit_logs[0].payload.get("revision_label") == "A"
    assert audit_logs[0].payload.get("change_note") == "Audit test revision"


def test_audit_log_contains_user_id(client, admin_token, admin_user, db, project):
    """Audit log contains the user_id of the actor."""
    # Clear existing audit logs
    db.query(AuditLog).delete()
    db.commit()
    
    response = client.patch(
        f"/api/projects/{project.id}",
        json={"name": "Updated Name"},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    assert response.status_code == 200
    
    audit_log = db.query(AuditLog).filter(
        AuditLog.action_type == "project.update"
    ).first()
    
    assert audit_log is not None
    assert audit_log.user_id == admin_user.id

