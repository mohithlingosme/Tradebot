"""FastAPI route unit tests for the market data ingestion service."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException

from market_data_ingestion.src import api


@pytest.mark.asyncio
async def test_health_check_reports_service_name():
    payload = await api.health_check()
    assert payload == {"status": "healthy", "service": "market-data-api"}


@pytest.mark.asyncio
async def test_readiness_check_queries_database(monkeypatch):
    class _Cursor:
        async def fetchone(self):
            return (1,)

        async def close(self):
            pass

    class _Conn:
        def __init__(self):
            self.calls = 0

        async def execute(self, query: str):
            self.calls += 1
            return _Cursor()

    fake_conn = _Conn()
    monkeypatch.setattr(api, "storage", SimpleNamespace(conn=fake_conn))

    payload = await api.readiness_check()
    assert payload["status"] == "ready"
    assert fake_conn.calls == 1


@pytest.mark.asyncio
async def test_readiness_check_propagates_errors(monkeypatch):
    class _Conn:
        async def execute(self, *_):
            raise RuntimeError("boom")

    monkeypatch.setattr(api, "storage", SimpleNamespace(conn=_Conn()))

    with pytest.raises(HTTPException) as exc:
        await api.readiness_check()

    assert exc.value.status_code == 503


@pytest.mark.asyncio
async def test_get_candles_returns_payload(monkeypatch):
    candles = [{"ts_utc": "2024-01-01", "close": 100.0}]
    monkeypatch.setattr(
        api,
        "storage",
        SimpleNamespace(fetch_last_n_candles=AsyncMock(return_value=candles)),
    )

    payload = await api.get_candles(symbol="AAPL", interval="1m", limit=1)
    assert payload["count"] == 1
    assert payload["data"] == candles


@pytest.mark.asyncio
async def test_get_candles_raises_when_no_data(monkeypatch):
    monkeypatch.setattr(
        api,
        "storage",
        SimpleNamespace(fetch_last_n_candles=AsyncMock(return_value=[])),
    )

    with pytest.raises(HTTPException) as exc:
        await api.get_candles(symbol="AAPL")

    assert exc.value.status_code == 404
