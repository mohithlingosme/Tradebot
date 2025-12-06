"""Tests covering websocket based adapters (kite/mock)."""

from __future__ import annotations

import asyncio
from datetime import timezone

import pytest

from market_data_ingestion.adapters.kite_ws import KiteWebSocketAdapter


def _adapter() -> KiteWebSocketAdapter:
    return KiteWebSocketAdapter(
        {
            "api_key": "demo",
            "api_secret": "demo",
            "websocket_url": "ws://localhost:8765",
            "reconnect_interval": 1,
        }
    )


def test_kite_adapter_normalizes_ticks():
    adapter = _adapter()
    payload = {
        "instrument_token": "MCX:GOLD",
        "timestamp": "2024-01-01T09:15:00Z",
        "last_price": 60250.5,
        "volume": 5,
    }
    tick = adapter._normalize_data(payload)
    assert tick.symbol == "MCX:GOLD"
    assert tick.provider == "kite"
    assert tick.price == pytest.approx(60250.5)
    assert tick.ts_utc.tzinfo == timezone.utc


@pytest.mark.asyncio
async def test_process_message_returns_none_for_invalid_json():
    adapter = _adapter()
    result = await adapter.process_message("not-json")
    assert result is None


@pytest.mark.asyncio
async def test_process_message_uses_normalizer(monkeypatch):
    adapter = _adapter()
    normalized = object()

    async def _fake_normalize(data):
        return normalized

    monkeypatch.setattr(adapter, "_normalize_data", lambda *_: normalized)
    result = await adapter.process_message('{"last_price": 100}')
    assert result is normalized
