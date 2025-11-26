from datetime import datetime, timedelta, timezone

import pytest

from common.market_data import normalize_to_candles


def _dummy_record(ts: datetime, close: float = 100.0) -> dict:
    return {
        "timestamp": ts,
        "open": close - 1,
        "high": close + 1,
        "low": close - 2,
        "close": close,
        "volume": 10,
    }


def test_normalize_drops_future_candles():
    now = datetime.now(timezone.utc)
    raw = [
        _dummy_record(now - timedelta(minutes=2), close=101),
        _dummy_record(now + timedelta(minutes=5), close=105),  # future record
    ]

    candles = normalize_to_candles(raw, symbol="TEST", timeframe="1m", source="unit")

    assert candles, "Expected at least one candle after normalization"
    assert all(candle.timestamp <= now for candle in candles)


def test_normalize_sorts_by_timestamp():
    now = datetime.now(timezone.utc)
    raw = [
        _dummy_record(now - timedelta(minutes=1), close=101),
        _dummy_record(now - timedelta(minutes=3), close=99),
        _dummy_record(now - timedelta(minutes=2), close=100),
    ]

    candles = normalize_to_candles(raw, symbol="TEST", timeframe="1m", source="unit")
    timestamps = [c.timestamp for c in candles]

    assert timestamps == sorted(timestamps)
    assert len(timestamps) == len(raw)

