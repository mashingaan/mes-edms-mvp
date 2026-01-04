import pytest

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
def item_for_responsible(db, project, responsible_user):
    """Create test item assigned to responsible user."""
    item = Item(
        project_id=project.id,
        part_number="TEST-002",
        name="Test Item",
        responsible_id=responsible_user.id,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@pytest.fixture
def unassigned_item(db, project):
    """Create test item without responsible user."""
    item = Item(
        project_id=project.id,
        part_number="TEST-003",
        name="Unassigned Item",
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def test_update_progress_as_responsible(client, responsible_token, item_for_responsible):
    """Responsible user can update progress for assigned item."""
    response = client.patch(
        f"/api/items/{item_for_responsible.id}/progress",
        json={"new_progress": 50, "comment": "Halfway done"},
        headers={"Authorization": f"Bearer {responsible_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["current_progress"] == 50


def test_update_progress_as_admin(client, admin_token, item_for_responsible):
    """Admin can update progress for any item."""
    response = client.patch(
        f"/api/items/{item_for_responsible.id}/progress",
        json={"new_progress": 75},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["current_progress"] == 75


def test_update_progress_as_viewer(client, viewer_token, item_for_responsible):
    """Viewer cannot update progress."""
    response = client.patch(
        f"/api/items/{item_for_responsible.id}/progress",
        json={"new_progress": 50},
        headers={"Authorization": f"Bearer {viewer_token}"}
    )
    
    assert response.status_code == 403


def test_update_progress_invalid_value(client, admin_token, item_for_responsible):
    """Progress value out of range is rejected."""
    response = client.patch(
        f"/api/items/{item_for_responsible.id}/progress",
        json={"new_progress": 150},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    assert response.status_code == 422  # Validation error


def test_progress_history(client, admin_token, item_for_responsible):
    """Progress history is logged."""
    # Update progress twice
    client.patch(
        f"/api/items/{item_for_responsible.id}/progress",
        json={"new_progress": 25, "comment": "First update"},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    client.patch(
        f"/api/items/{item_for_responsible.id}/progress",
        json={"new_progress": 50, "comment": "Second update"},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    # Get history
    response = client.get(
        f"/api/items/{item_for_responsible.id}/progress-history",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    assert response.status_code == 200
    history = response.json()
    assert len(history) == 2
    
    # Most recent first
    assert history[0]["new_progress"] == 50
    assert history[0]["old_progress"] == 25
    assert history[1]["new_progress"] == 25
    assert history[1]["old_progress"] == 0


def test_responsible_cannot_update_other_item(client, responsible_token, unassigned_item):
    """Responsible user cannot update progress for unassigned item."""
    response = client.patch(
        f"/api/items/{unassigned_item.id}/progress",
        json={"new_progress": 50},
        headers={"Authorization": f"Bearer {responsible_token}"}
    )
    
    assert response.status_code == 403


def test_notification_created_on_progress_update(client, admin_token, admin_user, item_for_responsible, db):
    """Notification is created for admins when progress is updated."""
    # Clear existing notifications
    db.query(Notification).delete()
    db.commit()
    
    response = client.patch(
        f"/api/items/{item_for_responsible.id}/progress",
        json={"new_progress": 50, "comment": "Halfway done"},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    assert response.status_code == 200
    
    # Check notification was created for admin
    notifications = db.query(Notification).filter(
        Notification.user_id == admin_user.id
    ).all()
    
    assert len(notifications) >= 1
    assert "0%" in notifications[0].message and "50%" in notifications[0].message
    assert item_for_responsible.part_number in notifications[0].message


def test_notification_payload_on_progress_update(client, admin_token, admin_user, item_for_responsible, db):
    """Notification payload contains correct progress info."""
    # Clear existing notifications
    db.query(Notification).delete()
    db.commit()
    
    response = client.patch(
        f"/api/items/{item_for_responsible.id}/progress",
        json={"new_progress": 75},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    assert response.status_code == 200
    
    # Check notification payload
    notification = db.query(Notification).filter(
        Notification.user_id == admin_user.id
    ).first()
    
    assert notification is not None
    assert notification.event_payload is not None
    assert notification.event_payload["old_progress"] == 0
    assert notification.event_payload["new_progress"] == 75
    assert notification.event_payload["item_id"] == str(item_for_responsible.id)

