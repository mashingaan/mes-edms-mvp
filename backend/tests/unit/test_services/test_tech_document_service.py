import pytest
from uuid import uuid4

from app.models.project import Project
from app.models.project_section import ProjectSection
from app.models.tech_document import TechDocument
from app.models.tech_document_version import TechDocumentVersion
from app.services import tech_document_service


class FakeUploadFile:
    def __init__(self, filename: str):
        self.filename = filename


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


@pytest.mark.asyncio
async def test_upload_document(db, section, admin_user, monkeypatch):
    fake_info = {
        "uuid": uuid4(),
        "sha256": "a" * 64,
        "size_bytes": 1234,
        "extension": ".xlsx",
    }

    async def fake_save(file):
        return fake_info

    monkeypatch.setattr(tech_document_service, "save_excel_file", fake_save)
    monkeypatch.setattr(tech_document_service, "delete_excel_file", lambda *args, **kwargs: None)

    document = await tech_document_service.upload_document(
        db,
        section.id,
        FakeUploadFile("test.xlsx"),
        admin_user.id
    )

    assert document.section_id == section.id
    assert document.filename == "test.xlsx"
    assert document.version == 1
    assert document.is_current is True
    assert document.created_by == admin_user.id


def test_list_documents(db, section, admin_user):
    doc_current = TechDocument(
        section_id=section.id,
        filename="current.xlsx",
        storage_uuid=uuid4(),
        file_extension=".xlsx",
        size_bytes=100,
        sha256="b" * 64,
        version=1,
        is_current=True,
        created_by=admin_user.id,
    )
    doc_deleted = TechDocument(
        section_id=section.id,
        filename="deleted.xlsx",
        storage_uuid=uuid4(),
        file_extension=".xlsx",
        size_bytes=100,
        sha256="c" * 64,
        version=1,
        is_current=True,
        created_by=admin_user.id,
        is_deleted=True,
    )
    doc_old = TechDocument(
        section_id=section.id,
        filename="old.xlsx",
        storage_uuid=uuid4(),
        file_extension=".xlsx",
        size_bytes=100,
        sha256="d" * 64,
        version=1,
        is_current=False,
        created_by=admin_user.id,
    )

    db.add_all([doc_current, doc_deleted, doc_old])
    db.commit()

    documents = tech_document_service.list_documents(db, section.id)

    assert len(documents) == 1
    assert documents[0].id == doc_current.id


@pytest.mark.asyncio
async def test_update_document_creates_version(db, section, admin_user, monkeypatch):
    document = TechDocument(
        section_id=section.id,
        filename="original.xlsx",
        storage_uuid=uuid4(),
        file_extension=".xlsx",
        size_bytes=100,
        sha256="e" * 64,
        version=1,
        is_current=True,
        created_by=admin_user.id,
    )
    db.add(document)
    db.commit()
    db.refresh(document)
    old_storage_uuid = document.storage_uuid

    new_info = {
        "uuid": uuid4(),
        "sha256": "f" * 64,
        "size_bytes": 200,
        "extension": ".xlsx",
    }

    async def fake_save(file):
        return new_info

    monkeypatch.setattr(tech_document_service, "save_excel_file", fake_save)
    monkeypatch.setattr(tech_document_service, "delete_excel_file", lambda *args, **kwargs: None)

    updated = await tech_document_service.update_document(
        db,
        document.id,
        FakeUploadFile("updated.xlsx"),
        admin_user.id
    )

    versions = db.query(TechDocumentVersion).filter(
        TechDocumentVersion.document_id == document.id
    ).all()

    assert updated.version == 2
    assert updated.storage_uuid == new_info["uuid"]
    assert len(versions) == 1
    assert versions[0].version == 1
    assert versions[0].storage_uuid == old_storage_uuid


def test_delete_document_soft(db, section, admin_user):
    document = TechDocument(
        section_id=section.id,
        filename="to_delete.xlsx",
        storage_uuid=uuid4(),
        file_extension=".xlsx",
        size_bytes=100,
        sha256="g" * 64,
        version=1,
        is_current=True,
        created_by=admin_user.id,
    )
    db.add(document)
    db.commit()
    db.refresh(document)

    result = tech_document_service.delete_document(db, document.id, admin_user.id, "soft")

    db.refresh(document)
    assert result is True
    assert document.is_deleted is True
    assert document.deleted_by == admin_user.id


def test_list_versions(db, section, admin_user):
    document = TechDocument(
        section_id=section.id,
        filename="base.xlsx",
        storage_uuid=uuid4(),
        file_extension=".xlsx",
        size_bytes=100,
        sha256="h" * 64,
        version=2,
        is_current=True,
        created_by=admin_user.id,
    )
    db.add(document)
    db.commit()
    db.refresh(document)

    version1 = TechDocumentVersion(
        document_id=document.id,
        version=1,
        storage_uuid=uuid4(),
        filename="base.xlsx",
        file_extension=".xlsx",
        size_bytes=100,
        sha256="i" * 64,
        created_by=admin_user.id,
    )
    version2 = TechDocumentVersion(
        document_id=document.id,
        version=2,
        storage_uuid=uuid4(),
        filename="base.xlsx",
        file_extension=".xlsx",
        size_bytes=120,
        sha256="j" * 64,
        created_by=admin_user.id,
    )
    db.add_all([version1, version2])
    db.commit()

    versions = tech_document_service.list_versions(db, document.id)

    assert len(versions) == 2
    assert versions[0].version == 2
    assert versions[1].version == 1
