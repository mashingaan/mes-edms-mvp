"""Seed admin user

Revision ID: 20250101120001
Revises: 20250101120000
Create Date: 2025-01-01 12:00:01.000000

"""
from typing import Sequence, Union
import os

from alembic import op
import sqlalchemy as sa
from passlib.context import CryptContext

# revision identifiers, used by Alembic.
revision: str = '20250101120001'
down_revision: Union[str, None] = '20250101120000'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=12)


def upgrade() -> None:
    # Get admin credentials from environment variables
    admin_email = os.environ.get('ADMIN_EMAIL', 'admin@example.com')
    admin_password = os.environ.get('ADMIN_PASSWORD', 'adminpassword')
    admin_name = os.environ.get('ADMIN_NAME', 'Administrator')
    
    # Hash password
    password_hash = pwd_context.hash(admin_password)
    
    # Insert admin user
    op.execute(
        f"""
        INSERT INTO users (full_name, email, password_hash, role, is_active)
        VALUES ('{admin_name}', '{admin_email}', '{password_hash}', 'admin', true)
        ON CONFLICT (email) DO NOTHING
        """
    )


def downgrade() -> None:
    # Get admin email from environment
    admin_email = os.environ.get('ADMIN_EMAIL', 'admin@example.com')
    
    # Delete admin user
    op.execute(f"DELETE FROM users WHERE email = '{admin_email}'")

