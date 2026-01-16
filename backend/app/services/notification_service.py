from uuid import UUID
from typing import Optional, List, Any
from datetime import datetime

from sqlalchemy.orm import Session

from app.models.notification import Notification
from app.models.user import User, UserRole
from app.models.document import Document
from app.models.document_revision import DocumentRevision
from app.models.item import Item
from app.models.tech_document import TechDocument
from app.models.project_section import ProjectSection
from app.models.project import Project


def create_notification(
    db: Session,
    user_id: UUID,
    message: str,
    event_payload: Optional[dict[str, Any]] = None
) -> Notification:
    """Create a notification for a user."""
    notification = Notification(
        user_id=user_id,
        message=message,
        event_payload=event_payload,
    )
    db.add(notification)
    db.commit()
    db.refresh(notification)
    return notification


def get_user_notifications(db: Session, user_id: UUID) -> List[Notification]:
    """Get all notifications for a user."""
    return db.query(Notification).filter(
        Notification.user_id == user_id
    ).order_by(Notification.created_at.desc()).all()


def mark_notification_as_read(
    db: Session,
    notification_id: UUID,
    user_id: UUID
) -> Optional[Notification]:
    """Mark a notification as read."""
    notification = db.query(Notification).filter(
        Notification.id == notification_id,
        Notification.user_id == user_id
    ).first()
    
    if not notification:
        return None
    
    notification.read_at = datetime.utcnow()
    db.commit()
    db.refresh(notification)
    return notification


def mark_all_notifications_as_read(db: Session, user_id: UUID) -> None:
    """Mark all notifications as read for a user."""
    db.query(Notification).filter(
        Notification.user_id == user_id,
        Notification.read_at == None
    ).update({"read_at": datetime.utcnow()})
    db.commit()


def notify_revision_uploaded(
    db: Session,
    document: Document,
    revision: DocumentRevision
) -> None:
    """Notify responsible user and admins about new revision."""
    from app.services.item_service import get_item
    
    item = get_item(db, document.item_id)
    if not item:
        return
    
    message = f"Новая ревизия {revision.revision_label} загружена для документа {document.title}"
    payload = {
        "document_id": str(document.id),
        "revision_id": str(revision.id),
        "revision_label": revision.revision_label,
    }
    
    # Notify responsible user
    if item.responsible_id:
        create_notification(db, item.responsible_id, message, payload)
    
    # Notify all admins
    admins = db.query(User).filter(User.role == UserRole.admin, User.is_active == True).all()
    for admin in admins:
        # Don't notify if admin is the responsible user (avoid duplicate)
        if item.responsible_id and admin.id == item.responsible_id:
            continue
        create_notification(db, admin.id, message, payload)


def notify_progress_updated(
    db: Session,
    item: Item,
    old_progress: int,
    new_progress: int
) -> None:
    """Notify admins about progress update."""
    message = f"Прогресс изделия {item.part_number} изменён: {old_progress}% → {new_progress}%"
    payload = {
        "item_id": str(item.id),
        "part_number": item.part_number,
        "old_progress": old_progress,
        "new_progress": new_progress,
    }
    
    # Notify all admins
    admins = db.query(User).filter(User.role == UserRole.admin, User.is_active == True).all()
    for admin in admins:
        create_notification(db, admin.id, message, payload)


def notify_document_deleted(
    db: Session,
    document: Document,
    item: Item,
    mode: str
) -> None:
    """Notify responsible user and admins about document deletion."""
    message = f"Документ '{document.title}' удалён ({mode}) для изделия {item.part_number}"
    payload = {
        "document_id": str(document.id),
        "item_id": str(item.id),
        "title": document.title,
        "mode": mode,
    }
    
    # Notify responsible user
    if item.responsible_id:
        create_notification(db, item.responsible_id, message, payload)
    
    # Notify all admins (avoid duplicate if admin is responsible)
    admins = db.query(User).filter(User.role == UserRole.admin, User.is_active == True).all()
    for admin in admins:
        if item.responsible_id and admin.id == item.responsible_id:
            continue
        create_notification(db, admin.id, message, payload)


def notify_item_updated(
    db: Session,
    item: Item,
    old_values: dict,
    new_values: dict,
    updated_by_user_id: UUID
) -> None:
    """Notify responsible user and admins about item update (section change)."""
    from app.models.project_section import ProjectSection
    
    # Only notify if section_id changed
    if "section_id" not in old_values or old_values.get("section_id") == new_values.get("section_id"):
        return
    
    # Get new section code
    new_section_code = "Без раздела"
    if new_values.get("section_id"):
        new_section = db.query(ProjectSection).filter(
            ProjectSection.id == new_values["section_id"]
        ).first()
        if new_section:
            new_section_code = new_section.code
    
    message = f"Изделие {item.part_number} перемещено в раздел {new_section_code}"
    payload = {
        "item_id": str(item.id),
        "part_number": item.part_number,
        "old_section_id": str(old_values.get("section_id")) if old_values.get("section_id") else None,
        "new_section_id": str(new_values.get("section_id")) if new_values.get("section_id") else None,
    }
    
    # Notify responsible user
    if item.responsible_id and item.responsible_id != updated_by_user_id:
        create_notification(db, item.responsible_id, message, payload)
    
    # Notify all admins (avoid duplicate if admin is responsible or updated by)
    admins = db.query(User).filter(User.role == UserRole.admin, User.is_active == True).all()
    for admin in admins:
        if admin.id == updated_by_user_id:
            continue
        if item.responsible_id and admin.id == item.responsible_id:
            continue
        create_notification(db, admin.id, message, payload)


def notify_tech_document_uploaded(
    db: Session,
    document: TechDocument,
    section: ProjectSection
) -> None:
    """Notify admins and responsible users about tech document upload."""
    message = f"Технологический документ {document.filename} загружен для раздела {section.code}"
    payload = {
        "document_id": str(document.id),
        "section_id": str(section.id),
        "version": document.version,
    }

    responsible_id = getattr(section, "responsible_id", None)
    if responsible_id:
        create_notification(db, responsible_id, message, payload)

    admins = db.query(User).filter(User.role == UserRole.admin, User.is_active == True).all()
    for admin in admins:
        if responsible_id and admin.id == responsible_id:
            continue
        create_notification(db, admin.id, message, payload)


def notify_tech_document_updated(
    db: Session,
    document: TechDocument,
    section: ProjectSection,
    old_version: int,
    new_version: int
) -> None:
    """Notify admins and responsible users about tech document update."""
    message = f"Технологический документ {document.filename} обновлен: {old_version} → {new_version}"
    payload = {
        "document_id": str(document.id),
        "section_id": str(section.id),
        "version": new_version,
    }

    responsible_id = getattr(section, "responsible_id", None)
    if responsible_id:
        create_notification(db, responsible_id, message, payload)

    admins = db.query(User).filter(User.role == UserRole.admin, User.is_active == True).all()
    for admin in admins:
        if responsible_id and admin.id == responsible_id:
            continue
        create_notification(db, admin.id, message, payload)


def notify_tech_document_deleted(
    db: Session,
    document: TechDocument,
    section: ProjectSection
) -> None:
    """Notify admins and responsible users about tech document deletion."""
    message = 	f"Технологический документ {document.filename} удален из раздела {section.code}"
    payload = {
        "document_id": str(document.id),
        "section_id": str(section.id),
        "version": document.version,
    }

    responsible_id = getattr(section, "responsible_id", None)
    if responsible_id:
        create_notification(db, responsible_id, message, payload)

    admins = db.query(User).filter(User.role == UserRole.admin, User.is_active == True).all()
    for admin in admins:
        if responsible_id and admin.id == responsible_id:
            continue
        create_notification(db, admin.id, message, payload)


def notify_tech_section_created(
    db: Session,
    section: ProjectSection,
    project: Project
) -> None:
    """Notify admins and responsible users about tech section creation."""
    message = f"Создан раздел {section.code} в проекте {project.name}"
    payload = {
        "section_id": str(section.id),
        "project_id": str(project.id),
    }

    responsible_id = getattr(project, "responsible_id", None)
    if responsible_id:
        create_notification(db, responsible_id, message, payload)

    admins = db.query(User).filter(User.role == UserRole.admin, User.is_active == True).all()
    for admin in admins:
        if responsible_id and admin.id == responsible_id:
            continue
        create_notification(db, admin.id, message, payload)


def notify_tech_section_deleted(
    db: Session,
    section_id: UUID,
    section_code: str,
    project: Project
) -> None:
    """Notify admins and responsible users about tech section deletion."""
    message = f"Удален раздел {section_code} в проекте {project.name}"
    payload = {
        "section_id": str(section_id),
        "project_id": str(project.id),
    }

    responsible_id = getattr(project, "responsible_id", None)
    if responsible_id:
        create_notification(db, responsible_id, message, payload)

    admins = db.query(User).filter(User.role == UserRole.admin, User.is_active == True).all()
    for admin in admins:
        if responsible_id and admin.id == responsible_id:
            continue
        create_notification(db, admin.id, message, payload)
