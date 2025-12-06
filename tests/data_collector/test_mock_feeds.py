"""Tests for mock websocket feeds and realtime ingestion glue."""

from __future__ import annotations

import asyncio
import signal
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from data_collector.scripts.realtime import RealtimeIngestionManager
from market_data_ingestion.adapters.mock_ws import MockWebSocketServer


class _FakeWebSocket:
    def __init__(self):
        self.messages = []

    async def send(self, payload: str):
        self.messages.append(payload)


@pytest.mark.asyncio
async def test_mock_websocket_server_emits_ticks(monkeypatch):
    server = MockWebSocketServer()
    fake_ws = _FakeWebSocket()

    monkeypatch.setattr("market_data_ingestion.adapters.mock_ws.random.uniform", lambda *_: 0.0)
    monkeypatch.setattr("market_data_ingestion.adapters.mock_ws.asyncio.sleep", AsyncMock(return_value=None))

    task = asyncio.create_task(server.send_mock_data(fake_ws))
    await asyncio.sleep(0)  # allow loop to schedule once
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
    assert fake_ws.messages  # server pushed at least one payload


def test_signal_handler_schedules_stop(monkeypatch):
    manager = RealtimeIngestionManager(["AAPL"], "mock", "sqlite:///market_data.db")
    scheduled = {}

    def _fake_create_task(coro):
        scheduled["coro"] = coro
        return SimpleNamespace()

    monkeypatch.setattr(asyncio, "create_task", _fake_create_task)
    manager._signal_handler(signal.SIGINT, None)
    assert "coro" in scheduled
