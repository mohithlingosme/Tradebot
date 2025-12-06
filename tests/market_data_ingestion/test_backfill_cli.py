"""Tests for the market_data_ingestion/src/cli helper."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from market_data_ingestion.src import cli


def _fake_storage():
    return SimpleNamespace(
        connect=AsyncMock(),
        create_tables=AsyncMock(),
        disconnect=AsyncMock(),
    )


def _set_args(monkeypatch, argv):
    monkeypatch.setattr(cli, "sys", SimpleNamespace(argv=argv))


@pytest.mark.asyncio
async def test_backfill_api_command_executes(monkeypatch):
    _set_args(
        monkeypatch,
        [
            "cli.py",
            "backfill-api",
            "--adapter",
            "yfinance",
            "--symbols",
            "AAPL,MSFT",
            "--start",
            "2024-01-01",
            "--end",
            "2024-01-02",
        ],
    )
    monkeypatch.setattr(cli, "DataStorage", lambda *_: _fake_storage())
    mocked_backfill = AsyncMock()
    monkeypatch.setattr(cli, "backfill_api", mocked_backfill)

    await cli.main()
    mocked_backfill.assert_awaited()


@pytest.mark.asyncio
async def test_backfill_csv_command_ingests(monkeypatch):
    _set_args(
        monkeypatch,
        [
            "cli.py",
            "backfill-csv",
            "--url",
            "https://example.com/data.csv",
            "--provider",
            "mock",
        ],
    )
    monkeypatch.setattr(cli, "DataStorage", lambda *_: _fake_storage())
    monkeypatch.setattr(cli, "fetch_csv", AsyncMock(return_value="csv,data"))
    mocked_ingest = AsyncMock()
    monkeypatch.setattr(cli, "ingest_csv", mocked_ingest)

    await cli.main()
    mocked_ingest.assert_awaited()


@pytest.mark.asyncio
async def test_replay_dlq_command_invokes_handler(monkeypatch):
    _set_args(monkeypatch, ["cli.py", "replay-dlq", "--limit", "5"])
    monkeypatch.setattr(cli, "DataStorage", lambda *_: _fake_storage())
    mocked_replay = AsyncMock()
    monkeypatch.setattr(cli, "reprocess_dlq", mocked_replay)

    await cli.main()
    mocked_replay.assert_awaited()
