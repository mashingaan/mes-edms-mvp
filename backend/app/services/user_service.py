from uuid import UUID
from typing import Optional, List

from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate
from app.utils.security import hash_password


def create_user(db: Session, user_data: UserCreate) -> User:
    """Create a new user."""
    # Check if email already exists
    existing = db.query(User).filter(User.email == user_data.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    user = User(
        full_name=user_data.full_name,
        email=user_data.email,
        password_hash=hash_password(user_data.password),
        role=user_data.role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def get_user(db: Session, user_id: UUID) -> Optional[User]:
    """Get user by ID."""
    return db.query(User).filter(User.id == user_id).first()


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """Get user by email."""
    return db.query(User).filter(User.email == email).first()


def list_users(db: Session) -> List[User]:
    """List all users."""
    return db.query(User).all()


def update_user(db: Session, user_id: UUID, user_data: UserUpdate) -> Optional[User]:
    """Update user."""
    user = get_user(db, user_id)
    if not user:
        return None
    
    update_data = user_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(user, field, value)
    
    db.commit()
    db.refresh(user)
    return user


def deactivate_user(db: Session, user_id: UUID) -> Optional[User]:
    """Deactivate user (soft delete)."""
    user = get_user(db, user_id)
    if not user:
        return None
    
    user.is_active = False
    db.commit()
    db.refresh(user)
    return user

