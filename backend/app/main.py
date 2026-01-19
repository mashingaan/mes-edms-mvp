import logging

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.config import settings
from app.database import engine
from app.routers import auth, users, projects, items, documents, notifications, audit, tech_documents
from app.middleware.audit_middleware import AuditMiddleware

logger = logging.getLogger(__name__)

app = FastAPI(
    title="MES-EDMS MVP",
    description="Конструкторский модуль - Phase 1",
    version="1.0.0"
)

# Audit middleware (must be added before CORS)
app.add_middleware(AuditMiddleware)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(users.router, prefix="/api/users", tags=["users"])
app.include_router(projects.router, prefix="/api/projects", tags=["projects"])
app.include_router(items.router, prefix="/api/items", tags=["items"])
app.include_router(documents.router, prefix="/api/documents", tags=["documents"])
app.include_router(tech_documents.router, prefix="/api/tech", tags=["tech"])
app.include_router(notifications.router, prefix="/api/v1/notifications", tags=["notifications"])
app.include_router(audit.router, prefix="/api/audit", tags=["audit"])


@app.on_event("startup")
async def startup_db_healthcheck():
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except Exception:
        logger.error("Database startup healthcheck failed", exc_info=True)
        raise


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


@app.get("/healthz/db")
async def db_health_check():
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return {"status": "ok"}
    except Exception:
        logger.error("Database healthcheck failed", exc_info=True)
        raise HTTPException(status_code=500, detail="Database unavailable")

