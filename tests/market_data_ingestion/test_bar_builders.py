"""Tests for tick/candle aggregation helpers."""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock

import pytest

from market_data_ingestion.adapters.base import NormalizedTick
from market_data_ingestion.core import aggregator as agg_mod
from market_data_ingestion.core.aggregator import CandleAggregator, TickAggregator


def _tick(price: float, seconds: int = 0) -> NormalizedTick:
    return NormalizedTick(
        symbol="AAPL",
        ts_utc=datetime(2024, 1, 1, 9, 15, seconds, tzinfo=timezone.utc),
        price=price,
        volume=1.0,
        provider="mock",
        raw={},
    )


@pytest.mark.asyncio
async def test_candle_aggregator_emits_payload_for_each_interval():
    aggregator = CandleAggregator((1, 5))
    await aggregator.handle_tick(_tick(100.0))
    await aggregator.handle_tick(_tick(101.0, seconds=1))
    await aggregator.flush()

    emitted = []
    while aggregator.pending_candles():
        emitted.append(await aggregator.next_candle())

    assert emitted
    candle = emitted[0]
    assert candle["symbol"] == "AAPL"
    assert candle["open"] == 100.0
    assert candle["close"] == 101.0
    assert candle["interval"] == "1s"


@pytest.mark.asyncio
async def test_tick_aggregator_flushes_all_intervals(monkeypatch):
    captured = []

    async def _noop_flush(self, *_args, **_kwargs):
        captured.append(_kwargs.get("interval_label"))

    monkeypatch.setattr(agg_mod.TickAggregator, "_flush_interval_candles", _noop_flush, raising=False)

    aggregator = TickAggregator()
    await aggregator.aggregate_tick(
        {
            "symbol": "AAPL",
            "ts_utc": datetime(2024, 1, 1, 9, 15, tzinfo=timezone.utc).isoformat(),
            "price": 100.0,
            "volume": 5,
        }
    )
    await aggregator.flush_candles()

    assert {"1s", "5s", "1m"}.issubset(set(captured))
