import json
import logging
import time
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy.orm import Session

from app.models.user import User
from app.utils.security import verify_password, create_access_token
from app.config import settings

logger = logging.getLogger(__name__)


def _log(event: str, level: int = logging.INFO, **data) -> None:
    logger.log(level, "event=%s data=%s", event, json.dumps(data, ensure_ascii=False, default=str))


def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    """Authenticate user by email and password."""
    started_at = time.perf_counter()

    db_started_at = time.perf_counter()
    user = db.query(User).filter(User.email == email).first()
    db_query_ms = (time.perf_counter() - db_started_at) * 1000

    if not user:
        _log(
            "auth.authenticate_user.denied",
            email=email,
            reason="user_not_found",
            db_query_ms=round(db_query_ms, 2),
            total_ms=round((time.perf_counter() - started_at) * 1000, 2),
        )
        return None
    if not user.is_active:
        _log(
            "auth.authenticate_user.denied",
            email=email,
            user_id=str(user.id),
            reason="user_inactive",
            db_query_ms=round(db_query_ms, 2),
            total_ms=round((time.perf_counter() - started_at) * 1000, 2),
        )
        return None
    verify_started_at = time.perf_counter()
    password_ok = verify_password(password, user.password_hash)
    verify_ms = (time.perf_counter() - verify_started_at) * 1000
    if not password_ok:
        _log(
            "auth.authenticate_user.denied",
            email=email,
            user_id=str(user.id),
            reason="invalid_password",
            db_query_ms=round(db_query_ms, 2),
            verify_ms=round(verify_ms, 2),
            total_ms=round((time.perf_counter() - started_at) * 1000, 2),
        )
        return None
    _log(
        "auth.authenticate_user.success",
        email=email,
        user_id=str(user.id),
        role=getattr(user.role, "value", str(user.role)),
        db_query_ms=round(db_query_ms, 2),
        verify_ms=round(verify_ms, 2),
        total_ms=round((time.perf_counter() - started_at) * 1000, 2),
    )
    return user


def create_user_token(user: User) -> str:
    """Create JWT access token for user."""
    expires_delta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    token_data = {
        "sub": str(user.id),
        "role": user.role.value,
    }
    return create_access_token(token_data, expires_delta)

