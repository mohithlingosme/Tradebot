"""Tests for equity market data adapters (yfinance et al.)."""

from __future__ import annotations

from datetime import datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pandas as pd
import pytest

from market_data_ingestion.adapters.yfinance import YFinanceAdapter


def _sample_df() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"Open": 100.0, "High": 101.0, "Low": 99.5, "Close": 100.5, "Volume": 1000},
            {"Open": 101.0, "High": 102.5, "Low": 100.0, "Close": 101.5, "Volume": 1200},
        ],
        index=pd.to_datetime(
            [datetime(2024, 1, 1, 9, 15), datetime(2024, 1, 1, 9, 16)]
        ),
    )


def test_yfinance_normalize_data_produces_chronological_payload():
    adapter = YFinanceAdapter({"rate_limit_per_minute": 120})
    normalized = adapter._normalize_data("AAPL", _sample_df(), "1m", "yfinance")
    assert len(normalized) == 2
    assert normalized[0]["symbol"] == "AAPL"
    assert normalized[0]["ts_utc"].startswith("2024-01-01")
    assert normalized[0]["type"] == "candle"
    assert normalized[-1]["close"] == pytest.approx(101.5)


@pytest.mark.asyncio
async def test_fetch_historical_data_invokes_rate_limit(monkeypatch):
    adapter = YFinanceAdapter({"rate_limit_per_minute": 60})

    mocked_sleep = AsyncMock()
    monkeypatch.setattr("market_data_ingestion.adapters.yfinance.asyncio.sleep", mocked_sleep)
    monkeypatch.setattr(
        "market_data_ingestion.adapters.yfinance.yf",
        SimpleNamespace(download=lambda *_, **__: _sample_df()),
    )

    candles = await adapter.fetch_historical_data("AAPL", "2024-01-01", "2024-01-02", interval="1m")
    assert len(candles) == 2
    mocked_sleep.assert_awaited()
