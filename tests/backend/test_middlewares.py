"""Unit tests for backend security middleware helpers."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.app.security.middleware import EnforceHTTPSMiddleware, SecurityHeadersMiddleware


def _build_app(enforce_https: bool = False) -> FastAPI:
    app = FastAPI()
    app.add_middleware(SecurityHeadersMiddleware)
    if enforce_https:
        app.add_middleware(EnforceHTTPSMiddleware)

    @app.get("/ping")
    def ping():
        return {"status": "ok"}

    return app


def test_security_headers_middleware_injects_defaults():
    client = TestClient(_build_app())
    response = client.get("/ping")
    assert response.status_code == 200
    headers = response.headers
    assert headers["strict-transport-security"].startswith("max-age")
    assert headers["x-content-type-options"] == "nosniff"
    assert headers["x-frame-options"] == "DENY"
    assert headers["referrer-policy"] == "strict-origin-when-cross-origin"


def test_enforce_https_redirects_insecure_requests():
    client = TestClient(_build_app(enforce_https=True))
    response = client.get("/ping", allow_redirects=False)
    assert response.status_code == 307
    assert response.headers["location"].startswith("https://")
