"""Integration tests for project sections endpoints."""

import pytest
from app.models.project import Project
from app.models.project_section import ProjectSection
from app.models.item import Item


@pytest.fixture
def test_project(db, admin_user) -> Project:
    """Create test project."""
    project = Project(
        name="Test Project for Sections",
        description="Test Description",
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


class TestSectionCRUD:
    """Tests for section CRUD endpoints."""

    def test_admin_can_create_section(self, client, admin_token, test_project):
        """Test that admin can create a section."""
        response = client.post(
            f"/api/projects/{test_project.id}/sections",
            json={"code": "БНС.КМД"},
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200
        result = response.json()
        assert result["code"] == "БНС.КМД"
        assert result["project_id"] == str(test_project.id)
        assert "id" in result
        assert "created_at" in result

    def test_duplicate_section_returns_existing(self, client, admin_token, test_project, db):
        """Test that creating duplicate section code returns existing (idempotent)."""
        # Create section first
        section = ProjectSection(
            project_id=test_project.id,
            code="БНС.ТХ"
        )
        db.add(section)
        db.commit()
        db.refresh(section)
        
        # Try to create same section again
        response = client.post(
            f"/api/projects/{test_project.id}/sections",
            json={"code": "БНС.ТХ"},
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200
        result = response.json()
        assert result["id"] == str(section.id)
        assert result["code"] == "БНС.ТХ"

    def test_list_sections(self, client, admin_token, test_project, db):
        """Test listing sections for a project."""
        # Create sections
        section1 = ProjectSection(project_id=test_project.id, code="SEC.A")
        section2 = ProjectSection(project_id=test_project.id, code="SEC.B")
        db.add_all([section1, section2])
        db.commit()
        
        response = client.get(
            f"/api/projects/{test_project.id}/sections",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200
        result = response.json()
        assert len(result) == 2
        codes = [s["code"] for s in result]
        assert "SEC.A" in codes
        assert "SEC.B" in codes

    def test_viewer_can_list_sections(self, client, viewer_token, test_project, db):
        """Test that viewer can list sections."""
        section = ProjectSection(project_id=test_project.id, code="VIEW.SEC")
        db.add(section)
        db.commit()
        
        response = client.get(
            f"/api/projects/{test_project.id}/sections",
            headers={"Authorization": f"Bearer {viewer_token}"}
        )
        
        assert response.status_code == 200
        result = response.json()
        assert len(result) == 1
        assert result[0]["code"] == "VIEW.SEC"

    def test_responsible_cannot_create_section(self, client, responsible_token, test_project):
        """Test that responsible user cannot create sections."""
        response = client.post(
            f"/api/projects/{test_project.id}/sections",
            json={"code": "NEW.SEC"},
            headers={"Authorization": f"Bearer {responsible_token}"}
        )
        
        assert response.status_code == 403

    def test_viewer_cannot_create_section(self, client, viewer_token, test_project):
        """Test that viewer cannot create sections."""
        response = client.post(
            f"/api/projects/{test_project.id}/sections",
            json={"code": "NEW.SEC"},
            headers={"Authorization": f"Bearer {viewer_token}"}
        )
        
        assert response.status_code == 403

    def test_section_in_project_response(self, client, admin_token, test_project, db):
        """Test that sections are included in project detail response."""
        section = ProjectSection(project_id=test_project.id, code="PROJ.SEC")
        db.add(section)
        db.commit()
        
        response = client.get(
            f"/api/projects/{test_project.id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200
        result = response.json()
        assert "sections" in result
        assert len(result["sections"]) == 1
        assert result["sections"][0]["code"] == "PROJ.SEC"

    def test_create_section_audit_log(self, client, admin_token, test_project, db):
        """Test that section creation is logged in audit."""
        response = client.post(
            f"/api/projects/{test_project.id}/sections",
            json={"code": "AUDIT.SEC"},
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200
        
        from app.models.audit_log import AuditLog
        audit_entry = db.query(AuditLog).filter(
            AuditLog.action_type == "project.section_create"
        ).first()
        assert audit_entry is not None
        assert audit_entry.payload["code"] == "AUDIT.SEC"


class TestItemFilterBySection:
    """Tests for filtering items by section."""

    def test_filter_items_by_section(self, client, admin_token, test_project, db):
        """Test filtering items by section_id."""
        # Create section
        section = ProjectSection(project_id=test_project.id, code="FILTER.SEC")
        db.add(section)
        db.commit()
        db.refresh(section)
        
        # Create items - one with section, one without
        item_with_section = Item(
            project_id=test_project.id,
            section_id=section.id,
            part_number="111.111.111.111",
            name="With Section"
        )
        item_without_section = Item(
            project_id=test_project.id,
            section_id=None,
            part_number="222.222.222.222",
            name="Without Section"
        )
        db.add_all([item_with_section, item_without_section])
        db.commit()
        
        # Filter by section
        response = client.get(
            f"/api/items?project_id={test_project.id}&section_id={section.id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200
        result = response.json()
        assert len(result) == 1
        assert result[0]["part_number"] == "111.111.111.111"

    def test_get_all_items_no_section_filter(self, client, admin_token, test_project, db):
        """Test getting all items without section filter."""
        section = ProjectSection(project_id=test_project.id, code="ALL.SEC")
        db.add(section)
        db.commit()
        db.refresh(section)
        
        item1 = Item(project_id=test_project.id, section_id=section.id, part_number="AAA.AAA.AAA.AAA", name="Item A")
        item2 = Item(project_id=test_project.id, section_id=None, part_number="BBB.BBB.BBB.BBB", name="Item B")
        db.add_all([item1, item2])
        db.commit()
        
        response = client.get(
            f"/api/items?project_id={test_project.id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200
        result = response.json()
        assert len(result) == 2

    def test_item_response_includes_section(self, client, admin_token, test_project, db):
        """Test that item response includes section information."""
        section = ProjectSection(project_id=test_project.id, code="RESP.SEC")
        db.add(section)
        db.commit()
        db.refresh(section)
        
        item = Item(
            project_id=test_project.id,
            section_id=section.id,
            part_number="SEC.RES.111.222",
            name="Item with Section"
        )
        db.add(item)
        db.commit()
        db.refresh(item)
        
        response = client.get(
            f"/api/items/{item.id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200
        result = response.json()
        assert result["section_id"] == str(section.id)
        assert result["section"] is not None
        assert result["section"]["code"] == "RESP.SEC"

