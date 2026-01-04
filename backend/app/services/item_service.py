from uuid import UUID
from typing import Optional, List

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status

from app.models.item import Item
from app.models.project import Project
from app.models.user import User
from app.models.progress_history import ProgressHistory
from app.schemas.item import ItemCreate, ItemUpdate
from app.services.notification_service import notify_progress_updated


def create_item(db: Session, item_data: ItemCreate) -> Item:
    """Create a new item."""
    project = db.query(Project).filter(Project.id == item_data.project_id).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    if item_data.responsible_id:
        responsible = db.query(User).filter(
            User.id == item_data.responsible_id,
            User.is_active == True
        ).first()
        if not responsible:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Responsible user not found or inactive")

    item = Item(
        project_id=item_data.project_id,
        part_number=item_data.part_number,
        name=item_data.name,
        docs_completion_percent=item_data.docs_completion_percent,
        responsible_id=item_data.responsible_id,
        status=item_data.status,
    )
    db.add(item)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to create item due to invalid data")
    db.refresh(item)
    return item


def get_item(db: Session, item_id: UUID) -> Optional[Item]:
    """Get item by ID."""
    return db.query(Item).filter(Item.id == item_id).first()


def list_items(db: Session, project_id: Optional[UUID] = None, section_id: Optional[UUID] = None) -> List[Item]:
    """List items, optionally filtered by project and/or section."""
    query = db.query(Item)
    if project_id:
        query = query.filter(Item.project_id == project_id)
    if section_id:
        query = query.filter(Item.section_id == section_id)
    return query.all()


def update_item(db: Session, item_id: UUID, item_data: ItemUpdate) -> Optional[Item]:
    """Update item."""
    item = get_item(db, item_id)
    if not item:
        return None
    
    update_data = item_data.model_dump(exclude_unset=True)
    if "responsible_id" in update_data:
        responsible_id = update_data["responsible_id"]
        if responsible_id is not None:
            responsible = db.query(User).filter(
                User.id == responsible_id,
                User.is_active == True
            ).first()
            if not responsible:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Responsible user not found or inactive")
    for field, value in update_data.items():
        setattr(item, field, value)
    
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to update item due to invalid data")
    db.refresh(item)
    return item


def delete_item(db: Session, item_id: UUID) -> bool:
    """Delete item."""
    item = get_item(db, item_id)
    if not item:
        return False
    
    db.delete(item)
    db.commit()
    return True


def update_progress(
    db: Session,
    item_id: UUID,
    new_progress: int,
    user_id: UUID,
    comment: Optional[str] = None
) -> Optional[Item]:
    """Update item progress and log to history."""
    item = get_item(db, item_id)
    if not item:
        return None
    
    old_progress = item.current_progress
    
    # Create progress history entry
    history = ProgressHistory(
        item_id=item_id,
        old_progress=old_progress,
        new_progress=new_progress,
        changed_by=user_id,
        comment=comment,
    )
    db.add(history)
    
    # Update item progress
    item.current_progress = new_progress
    
    db.commit()
    db.refresh(item)
    
    # Notify admins about progress update
    notify_progress_updated(db, item, old_progress, new_progress)
    
    return item


def get_progress_history(db: Session, item_id: UUID) -> List[ProgressHistory]:
    """Get progress history for item."""
    return db.query(ProgressHistory).filter(
        ProgressHistory.item_id == item_id
    ).order_by(ProgressHistory.changed_at.desc()).all()

