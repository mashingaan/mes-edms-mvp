import io
import pytest
from openpyxl import Workbook

from app.models.project import Project
from app.models.project_section import ProjectSection
from app.models.tech_document import TechDocument
from app.models.audit_log import AuditLog
from app.models.notification import Notification


def build_excel_file() -> io.BytesIO:
    workbook = Workbook()
    sheet = workbook.active
    sheet.append(["A1", "B1"])
    sheet.append(["A2", "B2"])
    stream = io.BytesIO()
    workbook.save(stream)
    stream.seek(0)
    return stream


@pytest.fixture
def project(db):
    project = Project(name="Tech Project")
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


@pytest.fixture
def section(db, project):
    section = ProjectSection(project_id=project.id, code="TECH.SEC")
    db.add(section)
    db.commit()
    db.refresh(section)
    return section


def test_admin_can_upload_document(client, admin_token, section):
    excel_file = build_excel_file()
    files = {"file": ("test.xlsx", excel_file, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}

    response = client.post(
        f"/api/tech/sections/{section.id}/documents",
        files=files,
        headers={"Authorization": f"Bearer {admin_token}"}
    )

    assert response.status_code == 200
    result = response.json()
    assert result["filename"] == "test.xlsx"
    assert result["version"] == 1


def test_viewer_cannot_upload_document(client, viewer_token, section):
    excel_file = build_excel_file()
    files = {"file": ("test.xlsx", excel_file, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}

    response = client.post(
        f"/api/tech/sections/{section.id}/documents",
        files=files,
        headers={"Authorization": f"Bearer {viewer_token}"}
    )

    assert response.status_code == 403


def test_list_documents(client, admin_token, section):
    excel_file = build_excel_file()
    files = {"file": ("list.xlsx", excel_file, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}

    client.post(
        f"/api/tech/sections/{section.id}/documents",
        files=files,
        headers={"Authorization": f"Bearer {admin_token}"}
    )

    response = client.get(
        f"/api/tech/sections/{section.id}/documents",
        headers={"Authorization": f"Bearer {admin_token}"}
    )

    assert response.status_code == 200
    docs = response.json()
    assert len(docs) >= 1
    assert docs[0]["section_id"] == str(section.id)


def test_download_document(client, admin_token, section):
    excel_file = build_excel_file()
    files = {"file": ("download.xlsx", excel_file, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}

    response = client.post(
        f"/api/tech/sections/{section.id}/documents",
        files=files,
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    document_id = response.json()["id"]

    download = client.get(
        f"/api/tech/documents/{document_id}/download",
        headers={"Authorization": f"Bearer {admin_token}"}
    )

    assert download.status_code == 200
    content_disposition = download.headers.get("content-disposition", "")
    assert "download.xlsx" in content_disposition


def test_preview_document(client, admin_token, section):
    excel_file = build_excel_file()
    files = {"file": ("preview.xlsx", excel_file, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}

    response = client.post(
        f"/api/tech/sections/{section.id}/documents",
        files=files,
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    document_id = response.json()["id"]

    preview = client.get(
        f"/api/tech/documents/{document_id}/preview",
        headers={"Authorization": f"Bearer {admin_token}"}
    )

    assert preview.status_code == 200
    result = preview.json()
    assert result["filename"] == "preview.xlsx"
    assert len(result["sheets"]) == 1
    assert len(result["sheets"][0]["rows"]) >= 1


def test_update_document(client, admin_token, section):
    excel_file = build_excel_file()
    files = {"file": ("update.xlsx", excel_file, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}

    response = client.post(
        f"/api/tech/sections/{section.id}/documents",
        files=files,
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    document_id = response.json()["id"]

    new_excel = build_excel_file()
    update_files = {"file": ("update_v2.xlsx", new_excel, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}

    updated = client.put(
        f"/api/tech/documents/{document_id}",
        files=update_files,
        headers={"Authorization": f"Bearer {admin_token}"}
    )

    assert updated.status_code == 200
    assert updated.json()["version"] == 2


def test_delete_document(client, admin_token, section, db):
    excel_file = build_excel_file()
    files = {"file": ("delete.xlsx", excel_file, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}

    response = client.post(
        f"/api/tech/sections/{section.id}/documents",
        files=files,
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    document_id = response.json()["id"]

    deleted = client.delete(
        f"/api/tech/documents/{document_id}?mode=soft",
        headers={"Authorization": f"Bearer {admin_token}"}
    )

    assert deleted.status_code == 200
    document = db.query(TechDocument).filter(TechDocument.id == document_id).first()
    assert document is not None
    assert document.is_deleted is True


def test_audit_log_created(client, admin_token, section, db):
    db.query(AuditLog).delete()
    db.commit()

    excel_file = build_excel_file()
    files = {"file": ("audit.xlsx", excel_file, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}

    response = client.post(
        f"/api/tech/sections/{section.id}/documents",
        files=files,
        headers={"Authorization": f"Bearer {admin_token}"}
    )

    assert response.status_code == 200
    audit_entry = db.query(AuditLog).filter(
        AuditLog.action_type == "tech_document.upload"
    ).first()
    assert audit_entry is not None
    assert audit_entry.payload["section_id"] == str(section.id)


def test_notification_sent(client, admin_token, admin_user, section, db):
    db.query(Notification).delete()
    db.commit()

    excel_file = build_excel_file()
    files = {"file": ("notify.xlsx", excel_file, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}

    response = client.post(
        f"/api/tech/sections/{section.id}/documents",
        files=files,
        headers={"Authorization": f"Bearer {admin_token}"}
    )

    assert response.status_code == 200
    notifications = db.query(Notification).filter(
        Notification.user_id == admin_user.id
    ).all()
    assert len(notifications) >= 1
