from datetime import datetime
from pathlib import Path

from brain.backtest.runner import load_candles_from_csv


def test_load_candles_resamples_ticks(tmp_path):
    csv_path = tmp_path / "ticks.csv"
    csv_path.write_text(
        "timestamp,symbol,price,volume\n"
        "2024-01-01T09:30:00,TEST,100,1\n"
        "2024-01-01T09:30:10,TEST,101,2\n"
        "2024-01-01T09:31:05,TEST,102,1\n"
    )
    candles = load_candles_from_csv(csv_path, "TEST", timeframe_s=60)
    assert len(candles) == 2
    assert candles[0].open == 100
    assert candles[0].close == 101
    assert candles[1].close == 102
