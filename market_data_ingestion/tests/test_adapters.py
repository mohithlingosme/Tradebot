import os
import sys
from datetime import datetime, timezone

import pytest

repo_root = os.path.join(os.path.dirname(__file__), "..", "..")
sys.path.insert(0, repo_root)

from market_data_ingestion.adapters.kite_ws import KiteWebSocketAdapter
from market_data_ingestion.adapters.base import NormalizedTick


def test_kite_normalize():
    adapter = KiteWebSocketAdapter({"websocket_url": "ws://localhost:8765"})
    raw = {
        "instrument_token": "AAPL",
        "last_price": 123.45,
        "timestamp": "2024-01-01T10:00:00Z",
        "volume": 10,
    }
    tick = adapter._normalize_data(raw)
    assert tick.symbol == "AAPL"
    assert tick.price == 123.45
    assert tick.volume == 10
    assert tick.provider == "kite"
    assert tick.ts_utc.tzinfo == timezone.utc
