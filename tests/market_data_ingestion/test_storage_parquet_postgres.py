"""Hybrid storage tests covering postgres/sqlite + parquet export helpers."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pandas as pd
import pytest

from market_data_ingestion.core.storage import DataStorage


@pytest.mark.asyncio
async def test_postgres_connection_uses_asyncpg_pool(monkeypatch):
    acquired = SimpleNamespace(close=AsyncMock())

    async def _fake_pool(*_args, **_kwargs):
        class _Pool:
            async def acquire(self):
                return acquired

            async def release(self, *_):
                pass

            async def close(self):
                pass

        return _Pool()

    monkeypatch.setattr("market_data_ingestion.core.storage.asyncpg.create_pool", _fake_pool)

    storage = DataStorage("postgresql://postgres@localhost:5432/market_data")
    await storage.connect()
    assert storage.db_type == "postgresql"
    assert storage.conn is acquired


@pytest.mark.asyncio
async def test_sqlite_candles_can_be_dumped_to_parquet(tmp_path):
    db_path = tmp_path / "candles.db"
    storage = DataStorage(f"sqlite:///{db_path}")
    await storage.connect()
    await storage.create_tables()

    candle = {
        "symbol": "AAPL",
        "ts_utc": "2024-01-01T09:15:00Z",
        "open": 100.0,
        "high": 101.0,
        "low": 99.5,
        "close": 100.5,
        "volume": 1000,
        "provider": "yfinance",
    }
    await storage.insert_candle(candle)
    rows = await storage.fetch_last_n_candles("AAPL", "1m", limit=5)
    assert rows and rows[0]["symbol"] == "AAPL"

    df = pd.DataFrame(rows)
    parquet_path = tmp_path / "candles.parquet"
    with patch.object(pd.DataFrame, "to_parquet", autospec=True) as mocked:
        df.to_parquet(parquet_path, index=False)
        mocked.assert_called_once()

    await storage.disconnect()
