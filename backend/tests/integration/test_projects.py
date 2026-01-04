import pytest

from app.models.project import Project, ProjectStatus
from app.models.audit_log import AuditLog


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


def test_update_project_audit_log_with_old_values(client, admin_token, db, project):
    """Test that updating project is logged with old/new values."""
    new_name = "Updated Project Name"
    new_status = "on_hold"

    response = client.patch(
        f"/api/projects/{project.id}",
        json={"name": new_name, "status": new_status},
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == new_name
    assert data["status"] == new_status

    # Check audit log
    audit_log = db.query(AuditLog).filter(
        AuditLog.action_type == "project.update"
    ).order_by(AuditLog.timestamp.desc()).first()

    assert audit_log is not None
    assert "old_values" in audit_log.payload
    assert "new_values" in audit_log.payload
    assert audit_log.payload["old_values"]["name"] == "Test Project"
    assert audit_log.payload["old_values"]["status"] == "active"
    assert audit_log.payload["new_values"]["name"] == new_name
    assert audit_log.payload["new_values"]["status"] == new_status


def test_update_project_partial_audit_log(client, admin_token, db, project):
    """Test partial update of project has correct audit log."""
    new_description = "New Description"

    response = client.patch(
        f"/api/projects/{project.id}",
        json={"description": new_description},
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 200

    # Check audit log - only description should be in old/new values
    audit_log = db.query(AuditLog).filter(
        AuditLog.action_type == "project.update"
    ).order_by(AuditLog.timestamp.desc()).first()

    assert audit_log is not None
    assert "description" in audit_log.payload["old_values"]
    assert "description" in audit_log.payload["new_values"]
    # name and status should not be in old/new values since they weren't changed
    assert "name" not in audit_log.payload["old_values"]
    assert "status" not in audit_log.payload["old_values"]


def test_update_project_viewer_forbidden(client, viewer_token, project):
    """Test that viewer cannot update project."""
    response = client.patch(
        f"/api/projects/{project.id}",
        json={"name": "Hacked Name"},
        headers={"Authorization": f"Bearer {viewer_token}"},
    )

    assert response.status_code == 403


def test_update_project_not_found(client, admin_token):
    """Test updating non-existent project returns 404."""
    from uuid import uuid4
    
    fake_id = str(uuid4())
    response = client.patch(
        f"/api/projects/{fake_id}",
        json={"name": "New Name"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 404

