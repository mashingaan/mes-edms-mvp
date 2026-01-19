import json
import logging
from typing import List

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from jose import JWTError

from app.database import get_db
from app.models.user import User
from app.utils.security import decode_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")
logger = logging.getLogger(__name__)


def _log(event: str, level: int = logging.INFO, **data) -> None:
    logger.log(level, "event=%s data=%s", event, json.dumps(data, ensure_ascii=False, default=str))


def get_current_user(
    request: Request,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """Get current authenticated user from JWT token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = decode_token(token)
        user_id: str = payload.get("sub")
        if user_id is None:
            _log(
                "auth.token.invalid",
                level=logging.WARNING,
                reason="missing_sub",
                path=request.url.path,
                client_host=getattr(request.client, "host", None),
            )
            raise credentials_exception
    except JWTError as exc:
        _log(
            "auth.token.invalid",
            level=logging.WARNING,
            reason="jwt_error",
            error=str(exc),
            path=request.url.path,
            client_host=getattr(request.client, "host", None),
        )
        raise credentials_exception
    
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        _log(
            "auth.token.invalid",
            level=logging.WARNING,
            reason="user_not_found",
            user_id=user_id,
            path=request.url.path,
            client_host=getattr(request.client, "host", None),
        )
        raise credentials_exception
    
    if not user.is_active:
        _log(
            "auth.token.invalid",
            level=logging.WARNING,
            reason="user_inactive",
            user_id=str(user.id),
            path=request.url.path,
            client_host=getattr(request.client, "host", None),
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User is deactivated"
        )
    
    return user


def require_role(allowed_roles: List[str]):
    """Dependency factory for role-based access control."""
    def dependency(current_user: User = Depends(get_current_user)):
        if current_user.role.value not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )
        return current_user
    return dependency

