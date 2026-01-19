"""Seed admin user

Revision ID: 20250101120001
Revises: 20250101120000
Create Date: 2025-01-01 12:00:01.000000

"""
import logging
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from passlib.context import CryptContext

from app.config import settings

# revision identifiers, used by Alembic.
revision: str = '20250101120001'
down_revision: Union[str, None] = '20250101120000'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=12)
logger = logging.getLogger("alembic.runtime.migration")


def upgrade() -> None:
    # Get admin credentials from settings (.env)
    admin_email = settings.ADMIN_EMAIL
    admin_password = settings.ADMIN_PASSWORD
    admin_name = settings.ADMIN_NAME
    
    bind = op.get_bind()
    existing_admin = bind.execute(
        sa.text("SELECT id FROM users WHERE email = :email"),
        {"email": admin_email},
    ).fetchone()
    if existing_admin:
        logger.info("Admin user already exists (%s). Skipping seed.", admin_email)
        return

    # Hash password
    password_hash = pwd_context.hash(admin_password)
    
    # Insert admin user (do not overwrite existing password hash)
    result = bind.execute(
        sa.text(
            """
            INSERT INTO users (full_name, email, password_hash, role, is_active)
            VALUES (:full_name, :email, :password_hash, 'admin', true)
            ON CONFLICT (email) DO NOTHING
            """
        ),
        {"full_name": admin_name, "email": admin_email, "password_hash": password_hash},
    )
    if getattr(result, "rowcount", 0) == 1:
        logger.info("Admin user created (%s).", admin_email)
    else:
        logger.info("Admin user seed skipped (%s).", admin_email)


def downgrade() -> None:
    # Get admin email from settings (.env)
    admin_email = settings.ADMIN_EMAIL
    admin_name = settings.ADMIN_NAME
    admin_password = settings.ADMIN_PASSWORD
    
    bind = op.get_bind()
    existing_admin = bind.execute(
        sa.text(
            """
            SELECT full_name, password_hash, role
            FROM users
            WHERE email = :email
            """
        ),
        {"email": admin_email},
    ).fetchone()
    if not existing_admin:
        logger.info("Admin user not found (%s). Skipping delete.", admin_email)
        return

    if existing_admin.role != "admin":
        logger.info("User exists but is not admin (%s). Skipping delete.", admin_email)
        return

    should_delete = True
    if existing_admin.full_name != admin_name:
        should_delete = False
    else:
        try:
            should_delete = pwd_context.verify(admin_password, existing_admin.password_hash)
        except Exception:
            should_delete = False

    if not should_delete:
        logger.info("Admin user does not match seeded credentials (%s). Skipping delete.", admin_email)
        return

    result = bind.execute(sa.text("DELETE FROM users WHERE email = :email"), {"email": admin_email})
    if getattr(result, "rowcount", 0) == 1:
        logger.info("Admin user deleted (%s).", admin_email)
    else:
        logger.info("Admin user delete skipped (%s).", admin_email)

