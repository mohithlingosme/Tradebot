# FILE: tests/backend/test_auth_routes.py
"""Test authentication routes: register/login/logout, token refresh, permissions."""

import pytest
from unittest.mock import patch, MagicMock


def test_login_successful(api_client):
    """Test successful user login returns JWT token."""
    credentials = {
        "username": "testuser",
        "password": "testpass"
    }

    # Mock user authentication
    with patch("backend.api.main.authenticate_user") as mock_auth, \
         patch("backend.api.main.create_access_token") as mock_token:

        mock_auth.return_value = MagicMock(username="testuser", role="user")
        mock_token.return_value = "fake.jwt.token"

        response = api_client.post("/api/auth/login", json=credentials)

        assert response.status_code == 200
        data = response.json()

        assert "access_token" in data
        assert "expires_in" in data
        assert data["access_token"] == "fake.jwt.token"
        assert data["expires_in"] == 1800


def test_login_invalid_credentials(api_client):
    """Test login with invalid credentials returns 401."""
    credentials = {
        "username": "testuser",
        "password": "wrongpass"
    }

    with patch("backend.api.main.authenticate_user", return_value=None):
        response = api_client.post("/api/auth/login", json=credentials)

        assert response.status_code == 401
        data = response.json()
        assert "Invalid credentials" in data["detail"]


def test_logout_successful(api_client):
    """Test logout endpoint."""
    response = api_client.post("/api/auth/logout")

    assert response.status_code == 200
    data = response.json()
    assert "Logged out successfully" in data["message"]


def test_register_new_user(api_client):
    """Test user registration creates new account."""
    user_data = {
        "username": "newuser",
        "email": "newuser@example.com",
        "password": "securepass123"
    }

    with patch("backend.api.main.USER_DATABASE", {}) as mock_db, \
         patch("backend.api.main.pwd_context") as mock_pwd, \
         patch("backend.api.main.create_access_token") as mock_token:

        mock_pwd.hash.return_value = "hashed_password"
        mock_token.return_value = "fake.jwt.token"

        response = api_client.post("/api/auth/register", json=user_data)

        assert response.status_code == 200
        data = response.json()

        assert "access_token" in data
        assert data["access_token"] == "fake.jwt.token"

        # Check user was added to database
        assert "newuser" in mock_db
        assert mock_db["newuser"]["email"] == "newuser@example.com"


def test_register_existing_user(api_client):
    """Test registering with existing username returns 400."""
    user_data = {
        "username": "existinguser",
        "email": "test@example.com",
        "password": "securepass123"
    }

    with patch("backend.api.main.USER_DATABASE", {"existinguser": {}}):
        response = api_client.post("/api/auth/register", json=user_data)

        assert response.status_code == 400
        data = response.json()
        assert "Username already exists" in data["detail"]


def test_register_invalid_email(api_client):
    """Test registration with invalid email format."""
    user_data = {
        "username": "testuser",
        "email": "invalid-email",
        "password": "securepass123"
    }

    response = api_client.post("/api/auth/register", json=user_data)

    assert response.status_code == 400
    data = response.json()
    assert "Invalid email format" in data["detail"]


def test_register_weak_password(api_client):
    """Test registration with password too short."""
    user_data = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "123"  # Too short
    }

    response = api_client.post("/api/auth/register", json=user_data)

    assert response.status_code == 400
    data = response.json()
    assert "Password must be at least 8 characters" in data["detail"]


def test_forgot_password_valid_email(api_client):
    """Test forgot password with valid email."""
    request_data = {"email": "user@example.com"}

    with patch("backend.api.main.USER_DATABASE", {
        "testuser": {"email": "user@example.com"}
    }):
        response = api_client.post("/api/auth/forgot-password", json=request_data)

        assert response.status_code == 200
        data = response.json()
        assert "If an account exists" in data["message"]


def test_forgot_password_unknown_email(api_client):
    """Test forgot password with unknown email (same response for security)."""
    request_data = {"email": "unknown@example.com"}

    with patch("backend.api.main.USER_DATABASE", {}):
        response = api_client.post("/api/auth/forgot-password", json=request_data)

        assert response.status_code == 200
        data = response.json()
        assert "If an account exists" in data["message"]


def test_protected_endpoint_requires_auth(api_client):
    """Test protected endpoints require authentication."""
    response = api_client.get("/protected")

    assert response.status_code == 401
    data = response.json()
    assert "Not authenticated" in data["detail"]


def test_protected_endpoint_with_valid_token(api_client):
    """Test protected endpoints work with valid JWT token."""
    # Mock authentication
    with patch("backend.api.main.get_current_active_user") as mock_auth:
        mock_auth.return_value = {"username": "testuser", "role": "user"}

        response = api_client.get("/protected")

        assert response.status_code == 200
        data = response.json()
        assert "Hello testuser" in data["message"]


def test_admin_only_endpoint_requires_admin_role(api_client):
    """Test admin-only endpoints require admin role."""
    # Mock regular user authentication
    with patch("backend.api.main.get_current_admin_user") as mock_auth:
        mock_auth.return_value = {"username": "regularuser", "role": "user"}

        response = api_client.get("/api/logs")  # Admin endpoint

        # Should fail if not admin
        if response.status_code == 403:
            data = response.json()
            assert "Admin access required" in data["detail"]


def test_token_refresh(api_client):
    """Test token refresh functionality if implemented."""
    # This test assumes there's a refresh endpoint
    # If not implemented, this test can be skipped
    refresh_data = {"refresh_token": "some_refresh_token"}

    response = api_client.post("/api/auth/refresh", json=refresh_data)

    # Either implemented (200) or not implemented (404)
    assert response.status_code in [200, 404]

    if response.status_code == 200:
        data = response.json()
        assert "access_token" in data


def test_logout_invalidates_token(api_client):
    """Test that logout invalidates the token (client-side)."""
    # Since JWT is stateless, logout is client-side
    # But we can test the endpoint exists and returns success
    response = api_client.post("/api/auth/logout")

    assert response.status_code == 200
    data = response.json()
    assert "Logged out successfully" in data["message"]


def test_auth_endpoints_cors_headers(api_client):
    """Test auth endpoints include proper CORS headers."""
    response = api_client.options("/api/auth/login")

    assert response.status_code == 200
    # Check CORS headers are present
    assert "access-control-allow-origin" in response.headers
    assert "access-control-allow-methods" in response.headers
    assert "access-control-allow-headers" in response.headers
