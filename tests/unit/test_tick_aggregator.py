from datetime import datetime, timezone

import pytest

from market_data_ingestion.adapters.base import NormalizedTick
from market_data_ingestion.core.aggregator import CandleAggregator


def _tick(symbol: str, price: float, volume: float, second: int) -> NormalizedTick:
    ts = datetime(2024, 1, 1, 9, 30, second, tzinfo=timezone.utc)
    return NormalizedTick(
        symbol=symbol,
        ts_utc=ts,
        price=price,
        volume=volume,
        provider="test",
        raw={},
    )


@pytest.mark.asyncio
async def test_candle_aggregation_emits_expected_payloads():
    agg = CandleAggregator()

    await agg.handle_tick(_tick("NIFTY", 100.0, 10, 0))
    await agg.handle_tick(_tick("NIFTY", 101.0, 5, 0))
    # Trigger roll to next second (emits first candle)
    await agg.handle_tick(_tick("NIFTY", 102.0, 2, 1))

    first = await agg.next_candle()
    assert first["symbol"] == "NIFTY"
    assert first["interval"] == "1s"
    assert first["open"] == 100.0
    assert first["high"] == 101.0
    assert first["low"] == 100.0
    assert first["close"] == 101.0
    assert first["volume"] == 15

    # Flush remaining candles (should emit 5s + 60s intervals)
    await agg.flush()
    emitted = [first]
    while agg.pending_candles():
        emitted.append(await agg.next_candle())

    intervals = {c["interval"] for c in emitted}
    assert {"1s", "5s", "60s"}.issubset(intervals)
