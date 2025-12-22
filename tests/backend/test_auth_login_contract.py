from __future__ import annotations

import asyncio
import importlib

import httpx
import pytest

from models import Base, User


pytestmark = pytest.mark.real_auth


async def _run_login_contract(tmp_path, monkeypatch):
    db_path = tmp_path / "auth_contract.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite+aiosqlite:///{db_path}")

    database_module = importlib.import_module("backend.app.database")
    auth_module = importlib.import_module("backend.api.auth")
    main_module = importlib.import_module("backend.app.main")

    database = importlib.reload(database_module)
    auth_service = importlib.reload(auth_module)
    backend_main = importlib.reload(main_module)

    async with database.engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with database.async_session() as session:
        hashed = auth_service.pwd_context.hash("samplepass123")
        session.add(User(email="tester@example.com", hashed_password=hashed, is_active=True))
        await session.commit()

    transport = httpx.ASGITransport(app=backend_main.app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.post(
            "/auth/login",
            json={"username": "tester@example.com", "password": "samplepass123"},
        )

        assert response.status_code == 200
        payload = response.json()
        assert payload["token_type"] == "bearer"
        assert payload["access_token"]

        me_response = await client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {payload['access_token']}"},
        )
        assert me_response.status_code == 200
        assert me_response.json()["email"] == "tester@example.com"

    await database.engine.dispose()


def test_login_accepts_json_payload(tmp_path, monkeypatch):
    asyncio.run(_run_login_contract(tmp_path, monkeypatch))
