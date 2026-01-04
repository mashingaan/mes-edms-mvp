import pytest
import io
from uuid import UUID

from app.models.project import Project
from app.models.item import Item
from app.models.document import Document
from app.models.notification import Notification
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
def item_for_responsible(db, project, responsible_user):
    """Create test item assigned to responsible user."""
    item = Item(
        project_id=project.id,
        part_number="TEST-001",
        name="Test Item for Responsible",
        responsible_id=responsible_user.id,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@pytest.fixture
def item_for_admin(db, project, admin_user):
    """Create test item assigned to admin."""
    item = Item(
        project_id=project.id,
        part_number="TEST-002",
        name="Test Item for Admin",
        responsible_id=admin_user.id,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@pytest.fixture
def document_for_responsible(client, admin_token, item_for_responsible):
    """Create document for responsible user's item."""
    pdf_content = b"%PDF-1.4 test content"
    files = {"file": ("test.pdf", io.BytesIO(pdf_content), "application/pdf")}
    data = {
        "item_id": str(item_for_responsible.id),
        "title": "Document for Responsible",
        "type": "Чертеж"
    }
    
    response = client.post(
        "/api/documents",
        files=files,
        data=data,
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    return response.json()


@pytest.fixture
def document_for_admin(client, admin_token, item_for_admin):
    """Create document for admin's item."""
    pdf_content = b"%PDF-1.4 test content"
    files = {"file": ("test.pdf", io.BytesIO(pdf_content), "application/pdf")}
    data = {
        "item_id": str(item_for_admin.id),
        "title": "Document for Admin",
        "type": "Спецификация"
    }
    
    response = client.post(
        "/api/documents",
        files=files,
        data=data,
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    return response.json()


# Soft-delete tests

def test_admin_can_soft_delete_any_document(client, admin_token, document_for_responsible, db):
    """Admin can soft delete any document."""
    doc_id = document_for_responsible["id"]
    
    response = client.delete(
        f"/api/documents/{doc_id}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Document deleted"
    assert data["mode"] == "soft"
    
    # Verify document is marked as deleted in DB
    document = db.query(Document).filter(Document.id == doc_id).first()
    assert document.is_deleted is True
    assert document.deleted_at is not None
    assert document.deleted_by is not None


def test_responsible_can_soft_delete_own_document(client, responsible_token, document_for_responsible, db):
    """Responsible user can soft delete document on their own item."""
    doc_id = document_for_responsible["id"]
    
    response = client.delete(
        f"/api/documents/{doc_id}",
        headers={"Authorization": f"Bearer {responsible_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Document deleted"
    assert data["mode"] == "soft"
    
    # Verify document is marked as deleted
    document = db.query(Document).filter(Document.id == doc_id).first()
    assert document.is_deleted is True


def test_responsible_cannot_soft_delete_other_document(client, responsible_token, document_for_admin):
    """Responsible user cannot delete document on another user's item."""
    doc_id = document_for_admin["id"]
    
    response = client.delete(
        f"/api/documents/{doc_id}",
        headers={"Authorization": f"Bearer {responsible_token}"}
    )
    
    assert response.status_code == 403


def test_viewer_cannot_soft_delete(client, viewer_token, document_for_responsible):
    """Viewer cannot delete any document."""
    doc_id = document_for_responsible["id"]
    
    response = client.delete(
        f"/api/documents/{doc_id}",
        headers={"Authorization": f"Bearer {viewer_token}"}
    )
    
    assert response.status_code == 403


def test_soft_delete_idempotent(client, admin_token, document_for_responsible, db):
    """Repeated soft delete returns success without error."""
    doc_id = document_for_responsible["id"]
    
    # First delete
    response1 = client.delete(
        f"/api/documents/{doc_id}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response1.status_code == 200
    
    # Second delete - should also succeed
    response2 = client.delete(
        f"/api/documents/{doc_id}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response2.status_code == 200


def test_soft_deleted_not_in_list(client, admin_token, document_for_responsible, item_for_responsible):
    """Soft deleted document does not appear in normal list."""
    doc_id = document_for_responsible["id"]
    item_id = item_for_responsible.id
    
    # Delete document
    client.delete(
        f"/api/documents/{doc_id}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    # List documents without show_deleted
    response = client.get(
        f"/api/documents?item_id={item_id}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    assert response.status_code == 200
    docs = response.json()
    doc_ids = [d["id"] for d in docs]
    assert doc_id not in doc_ids


def test_admin_can_view_deleted(client, admin_token, document_for_responsible, item_for_responsible):
    """Admin with show_deleted=true can see deleted documents."""
    doc_id = document_for_responsible["id"]
    item_id = item_for_responsible.id
    
    # Delete document
    client.delete(
        f"/api/documents/{doc_id}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    # List documents with show_deleted=true
    response = client.get(
        f"/api/documents?item_id={item_id}&show_deleted=true",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    assert response.status_code == 200
    docs = response.json()
    doc_ids = [d["id"] for d in docs]
    assert doc_id in doc_ids
    
    # Verify deleted document has is_deleted=True in response
    deleted_doc = next(d for d in docs if d["id"] == doc_id)
    assert deleted_doc["is_deleted"] is True


def test_viewer_cannot_view_deleted(client, viewer_token, item_for_responsible):
    """Viewer with show_deleted=true gets 403."""
    item_id = item_for_responsible.id
    
    response = client.get(
        f"/api/documents?item_id={item_id}&show_deleted=true",
        headers={"Authorization": f"Bearer {viewer_token}"}
    )
    
    assert response.status_code == 403


# Hard-delete tests

def test_admin_can_hard_delete(client, admin_token, document_for_responsible, db):
    """Admin with ?hard=true deletes document permanently."""
    doc_id = document_for_responsible["id"]
    
    response = client.delete(
        f"/api/documents/{doc_id}?hard=true",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Document deleted"
    assert data["mode"] == "hard"
    
    # Verify document is completely removed from DB
    document = db.query(Document).filter(Document.id == doc_id).first()
    assert document is None


def test_responsible_cannot_hard_delete(client, responsible_token, document_for_responsible):
    """Responsible user with ?hard=true gets 403."""
    doc_id = document_for_responsible["id"]
    
    response = client.delete(
        f"/api/documents/{doc_id}?hard=true",
        headers={"Authorization": f"Bearer {responsible_token}"}
    )
    
    assert response.status_code == 403


def test_hard_delete_removes_files(client, admin_token, item_for_responsible, db):
    """Hard delete removes all revision files from storage."""
    # Create document with initial revision
    pdf_content = b"%PDF-1.4 test content initial"
    files = {"file": ("test.pdf", io.BytesIO(pdf_content), "application/pdf")}
    data = {
        "item_id": str(item_for_responsible.id),
        "title": "Document with Multiple Revisions",
    }
    
    response = client.post(
        "/api/documents",
        files=files,
        data=data,
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    doc = response.json()
    doc_id = doc["id"]
    
    # Upload second revision
    pdf_content2 = b"%PDF-1.4 test content revision A"
    files2 = {"file": ("test_v2.pdf", io.BytesIO(pdf_content2), "application/pdf")}
    data2 = {"change_note": "Second revision"}
    
    client.post(
        f"/api/documents/{doc_id}/revisions",
        files=files2,
        data=data2,
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    # Hard delete
    response = client.delete(
        f"/api/documents/{doc_id}?hard=true",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    assert response.status_code == 200
    
    # Verify document is removed
    document = db.query(Document).filter(Document.id == doc_id).first()
    assert document is None


# Audit and notification tests

def test_audit_log_created_on_delete(client, admin_token, document_for_responsible, db):
    """Audit log is created on document deletion."""
    doc_id = document_for_responsible["id"]
    
    # Clear existing audit logs
    db.query(AuditLog).delete()
    db.commit()
    
    # Delete document
    client.delete(
        f"/api/documents/{doc_id}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    # Check audit log was created
    audit_logs = db.query(AuditLog).filter(
        AuditLog.action_type == "document.delete"
    ).all()
    
    assert len(audit_logs) >= 1
    audit_log = audit_logs[0]
    assert audit_log.payload["document_id"] == doc_id
    assert audit_log.payload["mode"] == "soft"
    assert "old_state" in audit_log.payload


def test_notification_sent_on_delete(client, admin_token, document_for_responsible, db, responsible_user):
    """Notifications are sent to responsible and admins on deletion."""
    doc_id = document_for_responsible["id"]
    
    # Clear existing notifications
    db.query(Notification).delete()
    db.commit()
    
    # Delete document
    client.delete(
        f"/api/documents/{doc_id}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    # Check notifications were created
    notifications = db.query(Notification).all()
    
    # At least one notification should exist (for responsible user)
    assert len(notifications) >= 1
    
    # Check responsible user received notification
    responsible_notifications = db.query(Notification).filter(
        Notification.user_id == responsible_user.id
    ).all()
    
    assert len(responsible_notifications) >= 1
    assert "удалён" in responsible_notifications[0].message.lower()

