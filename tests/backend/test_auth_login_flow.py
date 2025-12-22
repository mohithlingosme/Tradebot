from __future__ import annotations

import asyncio
import importlib

import pytest
from fastapi.testclient import TestClient

from models import Base, User


@pytest.mark.real_auth
def test_login_success_and_me_endpoint(tmp_path, monkeypatch):
    """Full login flow that hits /auth/login and /auth/me using a temporary SQLite DB."""
    db_path = tmp_path / "auth.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite+aiosqlite:///{db_path}")

    # Reload modules so the new DATABASE_URL is picked up.
    import backend.app.database as database_module
    import backend.api.auth as auth_module
    import backend.app.main as main_module

    database = importlib.reload(database_module)
    auth_service = importlib.reload(auth_module)
    backend_main = importlib.reload(main_module)

    async def seed_user():
        async with database.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        async with database.async_session() as session:
            hashed = auth_service.pwd_context.hash("samplepass123")
            session.add(User(email="tester@example.com", hashed_password=hashed, is_active=True))
            await session.commit()

    asyncio.run(seed_user())

    client = TestClient(backend_main.app)
    login_response = client.post(
        "/auth/login",
        json={"email": "tester@example.com", "password": "samplepass123"},
    )

    assert login_response.status_code == 200
    token = login_response.json()["access_token"]

    me_response = client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert me_response.status_code == 200
    assert me_response.json()["email"] == "tester@example.com"
