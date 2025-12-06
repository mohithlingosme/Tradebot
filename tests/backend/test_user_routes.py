"""Integration-style tests for primary user/auth routes."""

from __future__ import annotations

import uuid

import pytest

from backend.api.auth import USER_DATABASE


def _unique_username(prefix: str = "pytest") -> str:
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


def test_register_creates_user_and_returns_token(api_client):
    username = _unique_username()
    payload = {"username": username, "email": f"{username}@example.com", "password": "supersecret"}

    response = api_client.post("/auth/register", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert username in USER_DATABASE
    assert USER_DATABASE[username]["email"] == f"{username}@example.com"


def test_register_rejects_duplicate_username(api_client):
    username = _unique_username()
    payload = {"username": username, "email": f"{username}@example.com", "password": "duplicated!"}
    response = api_client.post("/auth/register", json=payload)
    assert response.status_code == 200

    duplicate = api_client.post("/auth/register", json=payload)

    assert duplicate.status_code == 400
    assert "exists" in duplicate.json()["detail"].lower()


@pytest.mark.parametrize(
    ("username", "password", "expected_status"),
    [
        ("user", "userpass", 200),
        ("user", "badpass", 401),
    ],
)
def test_login_enforces_credentials(api_client, username, password, expected_status):
    response = api_client.post("/auth/login", json={"username": username, "password": password})
    assert response.status_code == expected_status
    if expected_status == 200:
        assert "access_token" in response.json()
    else:
        assert "detail" in response.json()
