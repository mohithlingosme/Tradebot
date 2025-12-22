from datetime import datetime, timedelta

from data_engine.candle import Candle
from data_engine.indicators import calc_atr, calc_vwap


def build_candle(start: datetime, high: float, low: float, close: float) -> Candle:
    return Candle(
        symbol="TEST",
        timeframe_s=60,
        start_ts=start,
        end_ts=start + timedelta(seconds=59),
        open=close,
        high=high,
        low=low,
        close=close,
        volume=1.0,
        vwap=close,
    )


def test_calc_vwap_handles_zero_volume():
    assert calc_vwap([100.0, 101.0], [0.0, 0.0]) is None
    value = calc_vwap([100.0, 102.0], [1.0, 3.0])
    assert value == (100 * 1 + 102 * 3) / 4


def test_calc_atr_wilder_matches_expected_series():
    base = datetime(2024, 1, 1, 9, 30)
    data = [
        (10.0, 8.0, 9.0),
        (11.0, 9.0, 10.0),
        (12.0, 9.0, 11.0),
        (12.0, 10.0, 11.0),
        (13.0, 10.0, 12.0),
    ]
    candles = [build_candle(base + timedelta(minutes=i), h, l, c) for i, (h, l, c) in enumerate(data)]
    atr_values = calc_atr(candles, period=3, method="wilder")
    expected = [None, None, (2 + 2 + 3) / 3, ((7 / 3) * 2 + 2) / 3, (((((7 / 3) * 2 + 2) / 3) * 2) + 3) / 3]
    for idx, (value, exp) in enumerate(zip(atr_values, expected)):
        if exp is None:
            assert value is None
        else:
            assert value is not None
            assert abs(value - exp) < 1e-6
