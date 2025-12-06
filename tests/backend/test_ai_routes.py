"""Tests for the /api/ai/query endpoint that fronts the Finbot AI pipeline."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from ai_models.pipeline import AIResponse
from backend.app import routes_ai
from backend.app.main import app


@pytest.fixture(scope="module")
def backend_app_client() -> TestClient:
    return TestClient(app)


def test_ai_query_returns_answer(monkeypatch, backend_app_client):
    async def _fake_answer(*_, **__):
        return AIResponse(type="answer", content="Finbot is ready.", sources=["docs"])

    monkeypatch.setattr(routes_ai, "pipeline", type("P", (), {"answer": _fake_answer})())

    response = backend_app_client.post(
        "/api/ai/query",
        json={"question": "What is Finbot mode?", "user_id": "demo"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["type"] == "answer"
    assert payload["content"].startswith("Finbot")
    assert payload["sources"] == ["docs"]


def test_ai_query_validates_question(backend_app_client):
    response = backend_app_client.post("/api/ai/query", json={"question": ""})
    assert response.status_code == 400
    assert "required" in response.json()["detail"].lower()
