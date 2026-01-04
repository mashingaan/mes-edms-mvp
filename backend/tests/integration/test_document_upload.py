import pytest
import io
from uuid import UUID

from app.models.project import Project
from app.models.item import Item
from app.models.notification import Notification


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
        part_number="TEST-001",
        name="Test Item",
        responsible_id=responsible_user.id,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def test_upload_initial_revision(client, admin_token, item):
    """Upload PDF creates initial revision '-'."""
    pdf_content = b"%PDF-1.4 test content"
    files = {"file": ("test.pdf", io.BytesIO(pdf_content), "application/pdf")}
    data = {
        "item_id": str(item.id),
        "title": "Test Document",
        "type": "Чертеж"
    }
    
    response = client.post(
        "/api/documents",
        files=files,
        data=data,
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    assert response.status_code == 200
    doc = response.json()
    assert doc["title"] == "Test Document"
    assert doc["type"] == "Чертеж"
    # Verify current_revision is populated
    assert doc["current_revision"] is not None
    assert doc["current_revision"]["revision_label"] == "-"
    assert doc["current_revision"]["is_current"] is True
    # Verify revisions list is populated
    assert "revisions" in doc
    assert len(doc["revisions"]) == 1
    assert doc["revisions"][0]["revision_label"] == "-"


def test_upload_new_revision(client, admin_token, item):
    """Upload new revision increments label."""
    # First upload initial revision
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
    
    # Upload new revision
    pdf_content2 = b"%PDF-1.4 updated content"
    files2 = {"file": ("test_v2.pdf", io.BytesIO(pdf_content2), "application/pdf")}
    data2 = {"change_note": "Updated content"}
    
    response2 = client.post(
        f"/api/documents/{doc_id}/revisions",
        files=files2,
        data=data2,
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    assert response2.status_code == 200
    rev = response2.json()
    assert rev["revision_label"] == "A"
    assert rev["change_note"] == "Updated content"
    
    # Fetch document and verify revisions list
    response3 = client.get(
        f"/api/documents/{doc_id}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    assert response3.status_code == 200
    doc = response3.json()
    # Verify current_revision is the new revision
    assert doc["current_revision"] is not None
    assert doc["current_revision"]["revision_label"] == "A"
    assert doc["current_revision"]["is_current"] is True
    # Verify revisions list contains both revisions
    assert len(doc["revisions"]) == 2
    revision_labels = [r["revision_label"] for r in doc["revisions"]]
    assert "-" in revision_labels
    assert "A" in revision_labels


def test_upload_invalid_file(client, admin_token, item):
    """Upload non-PDF file is rejected."""
    exe_content = b"MZ this is an exe"
    files = {"file": ("test.exe", io.BytesIO(exe_content), "application/octet-stream")}
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
    
    assert response.status_code == 400


def test_upload_fake_pdf(client, admin_token, item):
    """Upload file with wrong magic bytes is rejected."""
    fake_pdf_content = b"This is not a PDF"
    files = {"file": ("test.pdf", io.BytesIO(fake_pdf_content), "application/pdf")}
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
    
    assert response.status_code == 400


def test_download_file_naming(client, admin_token, item):
    """Download returns correct filename."""
    # Upload document
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
    doc = response.json()
    doc_id = doc["id"]
    rev_id = doc["current_revision"]["id"]
    
    # Download
    response2 = client.get(
        f"/api/documents/{doc_id}/revisions/{rev_id}/download",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    assert response2.status_code == 200
    # Check filename in Content-Disposition header
    content_disposition = response2.headers.get("content-disposition", "")
    assert "TEST-001_-.pdf" in content_disposition


def test_list_documents_includes_revisions(client, admin_token, item):
    """List documents includes current_revision and revisions."""
    # Create a document
    pdf_content = b"%PDF-1.4 test content"
    files = {"file": ("test.pdf", io.BytesIO(pdf_content), "application/pdf")}
    data = {
        "item_id": str(item.id),
        "title": "Test Document",
    }
    
    client.post(
        "/api/documents",
        files=files,
        data=data,
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    # List documents
    response = client.get(
        f"/api/documents?item_id={item.id}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    assert response.status_code == 200
    docs = response.json()
    assert len(docs) >= 1
    
    doc = docs[0]
    # Verify current_revision is populated
    assert doc["current_revision"] is not None
    assert doc["current_revision"]["revision_label"] == "-"
    # Verify revisions list is populated
    assert "revisions" in doc
    assert len(doc["revisions"]) >= 1


def test_notification_created_on_initial_upload(client, admin_token, item, db, responsible_user):
    """Notification is created when initial document is uploaded."""
    # Clear existing notifications
    db.query(Notification).delete()
    db.commit()
    
    pdf_content = b"%PDF-1.4 test content"
    files = {"file": ("test.pdf", io.BytesIO(pdf_content), "application/pdf")}
    data = {
        "item_id": str(item.id),
        "title": "Test Document for Notification",
    }
    
    response = client.post(
        "/api/documents",
        files=files,
        data=data,
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    assert response.status_code == 200
    
    # Check notification was created for responsible user
    notifications = db.query(Notification).filter(
        Notification.user_id == responsible_user.id
    ).all()
    
    assert len(notifications) >= 1
    assert "ревизия" in notifications[0].message.lower() or "Новая ревизия" in notifications[0].message


def test_notification_created_on_new_revision(client, admin_token, item, db, responsible_user):
    """Notification is created when new revision is uploaded."""
    # First upload initial revision
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
    
    # Clear notifications
    db.query(Notification).delete()
    db.commit()
    
    # Upload new revision
    pdf_content2 = b"%PDF-1.4 updated content"
    files2 = {"file": ("test_v2.pdf", io.BytesIO(pdf_content2), "application/pdf")}
    data2 = {"change_note": "Updated content"}
    
    response2 = client.post(
        f"/api/documents/{doc_id}/revisions",
        files=files2,
        data=data2,
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    assert response2.status_code == 200
    
    # Check notification was created for responsible user
    notifications = db.query(Notification).filter(
        Notification.user_id == responsible_user.id
    ).all()
    
    assert len(notifications) >= 1
    assert "A" in notifications[0].message  # Revision A

