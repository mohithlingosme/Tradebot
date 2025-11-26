from datetime import datetime, timedelta, timezone

import pytest

from common.market_data import Candle, normalize_to_candles


def test_normalize_to_candles_orders_and_filters_future():
    now = datetime.now(timezone.utc)
    raw = [
        {"timestamp": now - timedelta(minutes=2), "open": 100, "high": 101, "low": 99, "close": 100, "volume": 10},
        {"timestamp": now - timedelta(minutes=1), "open": 101, "high": 102, "low": 100, "close": 101, "volume": 11},
        {"timestamp": now + timedelta(minutes=1), "open": 103, "high": 104, "low": 102, "close": 103, "volume": 12},  # future -> filtered
    ]

    candles = normalize_to_candles(raw, symbol="TEST", timeframe="1m", source="unit")
    assert len(candles) == 2
    assert all(isinstance(c, Candle) for c in candles)
    assert candles[0].timestamp < candles[1].timestamp
    assert candles[-1].timestamp <= now


def test_normalize_handles_empty_and_duplicates():
    candles = normalize_to_candles([], symbol="TEST", timeframe="1m", source="unit")
    assert candles == []

    ts = datetime(2024, 1, 1, tzinfo=timezone.utc)
    dup = [
        {"timestamp": ts, "open": 100, "high": 101, "low": 99, "close": 100, "volume": 10},
        {"timestamp": ts, "open": 100, "high": 101, "low": 99, "close": 100, "volume": 10},
    ]
    out = normalize_to_candles(dup, symbol="TEST", timeframe="1m", source="unit")
    assert len(out) == 2  # duplicates preserved but sorted
    assert all(c.timestamp == ts for c in out)


def test_normalize_rejects_missing_fields():
    bad = [{"timestamp": datetime(2024, 1, 1, tzinfo=timezone.utc), "open": 1, "high": 1, "low": 1}]
    with pytest.raises(ValueError):
        normalize_to_candles(bad, symbol="TEST", timeframe="1m", source="unit")
