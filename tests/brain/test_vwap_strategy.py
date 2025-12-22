from datetime import datetime, timedelta

from brain.strategies import VWAPMicrotrendConfig, VWAPMicrotrendStrategy
from data_engine.candle import Candle


def make_candle(start: datetime, price: float) -> Candle:
    return Candle(
        symbol="TEST",
        timeframe_s=60,
        start_ts=start,
        end_ts=start + timedelta(seconds=59),
        open=price,
        high=price,
        low=price,
        close=price,
        volume=1.0,
        vwap=None,
    )


def test_trend_detection_positive_negative():
    config = VWAPMicrotrendConfig(symbol="TEST", timeframe_s=60, trend_lookback=3)
    strategy = VWAPMicrotrendStrategy(None, "TEST", config=config)
    base = datetime(2024, 1, 1, 9, 45)
    for offset, price in enumerate([100, 101, 102]):
        candle = make_candle(base + timedelta(minutes=offset), price)
        strategy.window.append(candle)
    trend = strategy._compute_trend_value(3)
    assert trend > 0

    strategy.window.append(make_candle(base + timedelta(minutes=3), 99))
    trend2 = strategy._compute_trend_value(3)
    assert trend2 < 0


def test_first_15_min_filter_blocks_signals():
    config = VWAPMicrotrendConfig(symbol="TEST", timeframe_s=60, trend_lookback=3)
    strategy = VWAPMicrotrendStrategy(None, "TEST", config=config)
    base = datetime(2024, 1, 1, 9, 10)
    for offset, price in enumerate([100, 101, 102]):
        candle = make_candle(base + timedelta(minutes=offset), price)
        strategy.window.append(candle)
    candle = make_candle(datetime(2024, 1, 1, 9, 20), 103)
    signals = strategy.on_candle(candle)
    assert signals == []


def test_entry_and_exit_signals():
    config = VWAPMicrotrendConfig(symbol="TEST", timeframe_s=60, trend_lookback=3)
    strategy = VWAPMicrotrendStrategy(None, "TEST", config=config)
    start = datetime(2024, 1, 1, 9, 45)

    first = make_candle(start, 100)
    second = make_candle(start + timedelta(minutes=1), 101)
    third = make_candle(start + timedelta(minutes=2), 102)
    assert strategy.on_candle(first) == []
    assert strategy.on_candle(second) == []
    entry_signals = strategy.on_candle(third)
    assert entry_signals and entry_signals[0].action == "BUY"
    assert strategy.position == "LONG"

    exit_candle = make_candle(start + timedelta(minutes=3), 99)
    exit_signals = strategy.on_candle(exit_candle)
    assert len(exit_signals) == 1
    assert exit_signals[0].action == "CLOSE"
    assert strategy.position == "FLAT"
