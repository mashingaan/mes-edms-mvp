from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy.orm import Session

from app.models.user import User
from app.utils.security import verify_password, create_access_token
from app.config import settings


def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    """Authenticate user by email and password."""
    user = db.query(User).filter(User.email == email).first()
    if not user:
        return None
    if not user.is_active:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user


def create_user_token(user: User) -> str:
    """Create JWT access token for user."""
    expires_delta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    token_data = {
        "sub": str(user.id),
        "role": user.role.value,
    }
    return create_access_token(token_data, expires_delta)

