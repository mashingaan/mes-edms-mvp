"""Seed admin user

Revision ID: 20250101120001
Revises: 20250101120000
Create Date: 2025-01-01 12:00:01.000000

"""
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


def upgrade() -> None:
    # Get admin credentials from settings (.env)
    admin_email = settings.ADMIN_EMAIL
    admin_password = settings.ADMIN_PASSWORD
    admin_name = settings.ADMIN_NAME
    
    # Hash password
    password_hash = pwd_context.hash(admin_password)
    
    # Insert admin user or update existing credentials
    bind = op.get_bind()
    bind.execute(
        sa.text(
            """
            INSERT INTO users (full_name, email, password_hash, role, is_active)
            VALUES (:full_name, :email, :password_hash, 'admin', true)
            ON CONFLICT (email) DO UPDATE
            SET full_name = EXCLUDED.full_name,
                password_hash = EXCLUDED.password_hash
            """
        ),
        {"full_name": admin_name, "email": admin_email, "password_hash": password_hash},
    )


def downgrade() -> None:
    # Get admin email from settings (.env)
    admin_email = settings.ADMIN_EMAIL
    
    # Delete admin user
    bind = op.get_bind()
    bind.execute(sa.text("DELETE FROM users WHERE email = :email"), {"email": admin_email})

