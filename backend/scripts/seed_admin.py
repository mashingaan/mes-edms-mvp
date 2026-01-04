"""Script to create initial admin user."""
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal
from app.models.user import User, UserRole
from app.utils.security import hash_password
from app.config import settings


def seed_admin():
    """Create admin user if not exists."""
    db = SessionLocal()
    try:
        # Check if admin exists
        existing = db.query(User).filter(User.email == settings.ADMIN_EMAIL).first()
        if existing:
            print(f"Admin user {settings.ADMIN_EMAIL} already exists")
            return
        
        # Create admin user
        admin = User(
            full_name="Administrator",
            email=settings.ADMIN_EMAIL,
            password_hash=hash_password(settings.ADMIN_PASSWORD),
            role=UserRole.admin,
            is_active=True,
        )
        db.add(admin)
        db.commit()
        print(f"Admin user {settings.ADMIN_EMAIL} created successfully")
    finally:
        db.close()


if __name__ == "__main__":
    seed_admin()

