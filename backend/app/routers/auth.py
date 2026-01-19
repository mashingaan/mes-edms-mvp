import json
import logging
import time
from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.database import engine, get_db
from app.schemas.user import UserLogin, UserResponse, TokenResponse
from app.services.auth_service import authenticate_user, create_user_token
from app.dependencies import get_current_user
from app.models.user import User
from app.utils.security import create_access_token, decode_token

router = APIRouter()
logger = logging.getLogger(__name__)


def _log(event: str, level: int = logging.INFO, **data) -> None:
    logger.log(level, "event=%s data=%s", event, json.dumps(data, ensure_ascii=False, default=str))


@router.post("/login", response_model=TokenResponse)
def login(credentials: UserLogin, request: Request, db: Session = Depends(get_db)):
    _log(
        "auth.login.request",
        email=credentials.email,
        path=str(request.url.path),
        client_host=getattr(request.client, "host", None),
        user_agent=request.headers.get("user-agent"),
        request_id=request.headers.get("x-request-id"),
    )
    user = authenticate_user(db, credentials.email, credentials.password)
    if not user:
        _log(
            "auth.login.denied",
            level=logging.WARNING,
            email=credentials.email,
            path=str(request.url.path),
            client_host=getattr(request.client, "host", None),
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_user_token(user)
    _log(
        "auth.login.success",
        email=user.email,
        user_id=str(user.id),
        role=getattr(user.role, "value", str(user.role)),
        path=str(request.url.path),
        client_host=getattr(request.client, "host", None),
    )
    return TokenResponse(
        access_token=access_token,
        user=UserResponse.model_validate(user)
    )


@router.post("/logout")
def logout():
    # No-op for MVP - client clears token
    return {"message": "Logged out successfully"}


@router.get("/me", response_model=UserResponse)
def get_current_user_info(request: Request, current_user: User = Depends(get_current_user)):
    _log(
        "auth.me.request",
        user_id=str(current_user.id),
        role=getattr(current_user.role, "value", str(current_user.role)),
        path=str(request.url.path),
        client_host=getattr(request.client, "host", None),
    )
    return UserResponse.model_validate(current_user)


@router.get("/health")
def auth_health(request: Request):
    db_started_at = time.perf_counter()
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        db_ms = (time.perf_counter() - db_started_at) * 1000
    except Exception as exc:
        _log(
            "auth.health.db_error",
            level=logging.ERROR,
            path=str(request.url.path),
            client_host=getattr(request.client, "host", None),
            error=str(exc),
        )
        raise HTTPException(status_code=503, detail="Database unavailable")

    jwt_started_at = time.perf_counter()
    try:
        token = create_access_token(
            {"sub": "healthcheck", "role": "admin"},
            expires_delta=timedelta(seconds=5),
        )
        payload = decode_token(token)
        jwt_ms = (time.perf_counter() - jwt_started_at) * 1000
        if payload.get("sub") != "healthcheck":
            raise RuntimeError("Invalid token payload")
    except Exception as exc:
        _log(
            "auth.health.auth_error",
            level=logging.ERROR,
            path=str(request.url.path),
            client_host=getattr(request.client, "host", None),
            error=str(exc),
        )
        raise HTTPException(status_code=500, detail="Auth subsystem error")

    _log(
        "auth.health.ok",
        path=str(request.url.path),
        client_host=getattr(request.client, "host", None),
        db_ms=round(db_ms, 2),
        jwt_ms=round(jwt_ms, 2),
    )

    return {"status": "ok", "db": "ok", "auth": "ok", "db_ms": round(db_ms, 2), "jwt_ms": round(jwt_ms, 2)}

