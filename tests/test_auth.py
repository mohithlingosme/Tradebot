"""Test authentication functionality: login success/fail, /auth/me, inactive user block."""

import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.api.auth import get_current_active_user


@pytest.fixture
def client():
    return TestClient(app)


def test_login_success(client):
    """Test successful login returns token."""
    credentials = {"identifier": "test@example.com", "password": "password123"}

    with patch("backend.app.main.auth_service.authenticate_user") as mock_auth, \
         patch("backend.app.main.auth_service.create_access_token") as mock_token:

        mock_user = MagicMock()
        mock_user.email = "test@example.com"
        mock_auth.return_value = mock_user
        mock_token.return_value = "fake.jwt.token"

        response = client.post("/auth/login", json=credentials)

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["access_token"] == "fake.jwt.token"


def test_login_fail(client):
    """Test failed login returns 401."""
    credentials = {"identifier": "test@example.com", "password": "wrongpassword"}

    with patch("backend.app.main.auth_service.authenticate_user", return_value=None):
        response = client.post("/auth/login", json=credentials)

        assert response.status_code == 401
        data = response.json()
        assert "Invalid credentials" in data["detail"]


def test_auth_me_success(client):
    """Test /auth/me returns user info with valid token."""
    with patch("backend.app.main.auth_service.get_current_active_user") as mock_auth:
        mock_user = MagicMock()
        mock_user.username = "testuser"
        mock_user.email = "test@example.com"
        mock_user.role = "user"
        mock_auth.return_value = mock_user

        response = client.get("/auth/me")

        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "testuser"
        assert data["email"] == "test@example.com"


def test_auth_me_unauthenticated(client):
    """Test /auth/me requires authentication."""
    response = client.get("/auth/me")

    assert response.status_code == 401


def test_inactive_user_block(client):
    """Test inactive users are blocked from accessing protected endpoints."""
    with patch("backend.app.main.auth_service.get_current_active_user") as mock_auth:
        mock_auth.side_effect = Exception("User is inactive")

        response = client.get("/auth/me")

        assert response.status_code == 401
