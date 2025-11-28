import json
import os
from datetime import datetime, timedelta
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from jose import jwt

# Configure test-specific environment before importing the app
TEST_ROOT = Path(__file__).resolve().parent
BACKEND_TEST_DB_PATH_ENV = os.environ.get("BACKEND_TEST_DB_PATH")
TEST_DB_PATH = (
    Path(BACKEND_TEST_DB_PATH_ENV).resolve()
    if BACKEND_TEST_DB_PATH_ENV
    else (TEST_ROOT / "test_backend.db").resolve()
)
TEST_LOG_PATH = TEST_ROOT / "logs" / "test-finbot.log"
os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB_PATH}"
os.environ["LOG_FILE"] = str(TEST_LOG_PATH)
os.environ.setdefault("LOG_LEVEL", "DEBUG")

from backend.app.config import settings
from backend.app.core.security import create_access_token
from backend.app.main import app


def _cleanup_path(path: Path) -> None:
    if path.exists():
        path.unlink()


@pytest.fixture(scope="session", autouse=True)
def cleanup_test_artifacts():
    _cleanup_path(TEST_DB_PATH)
    _cleanup_path(TEST_LOG_PATH)
    yield
    _cleanup_path(TEST_DB_PATH)
    _cleanup_path(TEST_LOG_PATH)
    try:
        TEST_LOG_PATH.parent.rmdir()
    except OSError:
        pass


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def admin_token(client: TestClient) -> str:
    response = client.post(
        "/api/auth/login",
        json={
            "username": settings.default_admin_username,
            "password": settings.default_admin_password,
        },
    )
    assert response.status_code == 200
    return response.json()["access_token"]


@pytest.fixture
def user_token(client: TestClient) -> str:
    response = client.post(
        "/api/auth/login",
        json={
            "username": settings.default_user_username,
            "password": settings.default_user_password,
        },
    )
    assert response.status_code == 200
    return response.json()["access_token"]


def _auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _build_log_line(
    timestamp: datetime,
    level: str,
    component: str,
    message: str,
    data: dict | None = None,
    trace_id: str | None = None,
    duration_ms: float | None = None,
) -> str:
    pieces = [f"[{component}] {message}"]
    if data is not None:
        pieces.append(f"Data: {json.dumps(data)}")
    if trace_id:
        pieces.append(f"Trace: {trace_id}")
    if duration_ms is not None:
        pieces.append(f"Duration: {duration_ms:.2f}ms")
    payload = " | ".join(pieces)
    ts_text = timestamp.strftime("%Y-%m-%d %H:%M:%S,%f")
    return f"{ts_text} - backend.app.main - {level.upper()} - {payload}"


def _seed_logs(entries: list[str]) -> None:
    TEST_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with TEST_LOG_PATH.open("w", encoding="utf-8") as handle:
        handle.write("\n".join(entries))
        handle.write("\n")


def test_health_endpoints_exposed_without_auth(client: TestClient) -> None:
    assert client.get("/health").status_code == 200
    assert client.get("/api/health").status_code == 200


def test_metrics_requires_admin(client: TestClient, admin_token: str, user_token: str) -> None:
    assert client.get("/api/metrics").status_code == 401
    assert client.get("/api/metrics", headers=_auth_headers(user_token)).status_code == 403
    response = client.get("/api/metrics", headers=_auth_headers(admin_token))
    assert response.status_code == 200
    assert "active_strategies" in response.json()



@pytest.mark.parametrize(
    "path",
    ["/api/portfolio", "/api/positions", "/api/trades"],
)
def test_get_routes_require_auth(client: TestClient, path: str) -> None:
    response = client.get(path)
    assert response.status_code == 401


def test_protected_get_routes_accept_user_token(
    client: TestClient, user_token: str
) -> None:
    for path in ["/api/portfolio", "/api/positions", "/api/trades"]:
        response = client.get(path, headers=_auth_headers(user_token))
        assert response.status_code == 200
        assert response.json() is not None


def test_strategy_actions_require_auth(client: TestClient) -> None:
    response = client.post("/api/strategy/start", json={"strategy_id": "demo", "parameters": {}},)
    assert response.status_code == 401
    response = client.post("/api/strategy/stop", json={"instance_id": "demo"},)
    assert response.status_code == 401


def test_strategy_actions_accept_user_token(client: TestClient, user_token: str) -> None:
    response = client.post(
        "/api/strategy/start",
        headers=_auth_headers(user_token),
        json={"strategy_id": "demo", "parameters": {}},
    )
    assert response.status_code == 200
    response = client.post(
        "/api/strategy/stop",
        headers=_auth_headers(user_token),
        json={"instance_id": "demo"},
    )
    assert response.status_code == 200


def test_malformed_and_expired_tokens_are_rejected(client: TestClient, user_token: str) -> None:
    malformed = client.get("/api/portfolio", headers={"Authorization": "Bearer malformed"})
    assert malformed.status_code == 401

    payload = jwt.decode(
        user_token,
        settings.jwt_secret_key,
        algorithms=[settings.jwt_algorithm],
    )
    expired = create_access_token(
        data={"sub": payload["sub"], "role": payload.get("role", "user")},
        expires_delta=timedelta(seconds=-5),
    )
    expired_response = client.get("/api/portfolio", headers=_auth_headers(expired))
    assert expired_response.status_code == 401


def test_logs_restricted_to_admin(client: TestClient, user_token: str, admin_token: str) -> None:
    assert client.get("/api/logs").status_code == 401
    assert client.get("/api/logs", headers=_auth_headers(user_token)).status_code == 403

    now = datetime.utcnow()
    entries = [
        _build_log_line(now - timedelta(minutes=5), "info", "system", "start", {"order": "a1"}, "trace-a", 15.2),
        _build_log_line(now - timedelta(minutes=2), "warning", "strategy", "warn", {"order": "w1"}, "trace-b", 5.5),
        _build_log_line(now - timedelta(minutes=1), "error", "strategy", "fail", {"order": "e1", "token": "super"}, "trace-c", 28.7),
    ]
    _seed_logs(entries)

    params = {
        "level": "warning",
        "limit": 1,
        "since": (now - timedelta(minutes=3)).isoformat(),
        "until": (now + timedelta(seconds=5)).isoformat(),
    }
    response = client.get("/api/logs", headers=_auth_headers(admin_token), params=params)
    assert response.status_code == 200
    data = response.json()
    assert data["entries"]
    first = data["entries"][0]
    assert first["level"] == "ERROR"
    assert first["trace_id"] == "trace-c"
    assert first["extra"]["component"] == "strategy"
    assert first["extra"]["data"]["order"] == "e1"
    assert first["extra"]["data"]["token"] == "***REDACTED***"


def test_logs_returns_503_when_store_unavailable(client: TestClient, admin_token: str) -> None:
    _cleanup_path(TEST_LOG_PATH)

    response = client.get("/api/logs", headers=_auth_headers(admin_token))
    assert response.status_code == 503
    detail = response.json().get("detail", "")
    assert "log" in detail.lower() or "store" in detail.lower()
