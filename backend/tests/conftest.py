import os
import pytest
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

# Set test environment variables before importing app
os.environ["DATABASE_URL"] = "postgresql://postgres:postgres@localhost:5432/mes_edms_test"
os.environ["SECRET_KEY"] = "test-secret-key"
os.environ["FILE_STORAGE_PATH"] = "/tmp/mes_edms_test_storage"

from app.main import app
from app.database import Base, get_db
from app.models.user import User, UserRole
from app.utils.security import hash_password

# Test database
SQLALCHEMY_DATABASE_URL = os.environ["DATABASE_URL"]
engine = create_engine(SQLALCHEMY_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db() -> Generator:
    """Create test database session."""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db) -> Generator:
    """Create test client with database override."""
    def override_get_db():
        try:
            yield db
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def admin_user(db) -> User:
    """Create admin user for testing."""
    user = User(
        full_name="Test Admin",
        email="admin@test.com",
        password_hash=hash_password("testpassword123"),
        role=UserRole.admin,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def responsible_user(db) -> User:
    """Create responsible user for testing."""
    user = User(
        full_name="Test Responsible",
        email="responsible@test.com",
        password_hash=hash_password("testpassword123"),
        role=UserRole.responsible,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def viewer_user(db) -> User:
    """Create viewer user for testing."""
    user = User(
        full_name="Test Viewer",
        email="viewer@test.com",
        password_hash=hash_password("testpassword123"),
        role=UserRole.viewer,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def admin_token(client, admin_user) -> str:
    """Get access token for admin user."""
    response = client.post("/api/auth/login", json={
        "email": "admin@test.com",
        "password": "testpassword123"
    })
    return response.json()["access_token"]


@pytest.fixture
def responsible_token(client, responsible_user) -> str:
    """Get access token for responsible user."""
    response = client.post("/api/auth/login", json={
        "email": "responsible@test.com",
        "password": "testpassword123"
    })
    return response.json()["access_token"]


@pytest.fixture
def viewer_token(client, viewer_user) -> str:
    """Get access token for viewer user."""
    response = client.post("/api/auth/login", json={
        "email": "viewer@test.com",
        "password": "testpassword123"
    })
    return response.json()["access_token"]

