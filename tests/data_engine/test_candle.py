from datetime import datetime, timedelta

from data_engine.candle import Candle


def test_candle_update_tracks_high_low_and_vwap():
    ts = datetime(2024, 1, 1, 10, 0, 5)
    candle = Candle.from_tick("BTCUSD", timeframe_s=60, ts=ts, price=100.0, volume=2.0)
    assert candle.start_ts == datetime(2024, 1, 1, 10, 0, 0)
    assert candle.end_ts == ts
    assert candle.vwap == 100.0

    mid_ts = ts + timedelta(seconds=10)
    candle.update(price=105.0, volume=1.0, ts=mid_ts)
    assert candle.high == 105.0
    assert candle.low == 100.0
    assert candle.close == 105.0
    assert candle.volume == 3.0
    assert candle.vwap == (100 * 2 + 105 * 1) / 3

    assert not candle.is_complete(ts + timedelta(seconds=30))
    assert candle.is_complete(ts + timedelta(seconds=60))

    data = candle.to_dict()
    assert data["symbol"] == "BTCUSD"
    assert data["start_ts"].startswith("2024-01-01T10:00:00")
