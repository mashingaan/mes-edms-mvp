import pytest


def test_login_success(client, admin_user):
    """Valid credentials return tokens."""
    response = client.post("/api/auth/login", json={
        "email": "admin@test.com",
        "password": "testpassword123"
    })
    
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == "admin@test.com"
    assert data["user"]["role"] == "admin"


def test_login_invalid_password(client, admin_user):
    """Invalid password returns 401."""
    response = client.post("/api/auth/login", json={
        "email": "admin@test.com",
        "password": "wrongpassword"
    })
    
    assert response.status_code == 401


def test_login_invalid_email(client):
    """Non-existent user returns 401."""
    response = client.post("/api/auth/login", json={
        "email": "nonexistent@test.com",
        "password": "testpassword123"
    })
    
    assert response.status_code == 401


def test_protected_route_without_token(client):
    """Protected route without token returns 401."""
    response = client.get("/api/auth/me")
    
    assert response.status_code == 401


def test_protected_route_with_valid_token(client, admin_token):
    """Protected route with valid token works."""
    response = client.get("/api/auth/me", headers={
        "Authorization": f"Bearer {admin_token}"
    })
    
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "admin@test.com"


def test_protected_route_with_invalid_token(client):
    """Protected route with invalid token returns 401."""
    response = client.get("/api/auth/me", headers={
        "Authorization": "Bearer invalid-token"
    })
    
    assert response.status_code == 401


def test_logout(client, admin_token):
    """Logout endpoint works."""
    response = client.post("/api/auth/logout", headers={
        "Authorization": f"Bearer {admin_token}"
    })
    
    assert response.status_code == 200

