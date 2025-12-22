from datetime import datetime, timedelta

from data_engine.candle import Candle
from data_engine.live_engine import LiveDataEngine


def test_live_data_engine_emits_completed_candles():
    engine = LiveDataEngine(timeframe_s=60, window_size=5, logger=None)
    ts = datetime(2024, 1, 1, 9, 30, 5)

    current, completed = engine.on_tick("ETHUSD", ts, 2000.0, 1.0)
    assert completed is None
    assert isinstance(current, Candle)

    current2, completed2 = engine.on_tick("ETHUSD", ts + timedelta(seconds=10), 2005.0, 2.0)
    assert completed2 is None
    assert current2.close == 2005.0

    next_ts = ts + timedelta(seconds=65)
    current3, completed3 = engine.on_tick("ETHUSD", next_ts, 2010.0, 3.0)
    assert completed3 is not None
    assert completed3.close == 2005.0
    assert engine.window("ETHUSD").last == completed3
    assert current3.start_ts == datetime(2024, 1, 1, 9, 31, 0)
