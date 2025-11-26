from datetime import datetime, timedelta, timezone

import pytest

from common.market_data import Candle
from strategies.ema_crossover.strategy import EMACrossoverStrategy


def _make_candle(price: float, idx: int = 0, symbol: str = "TEST") -> Candle:
    ts = datetime(2024, 1, 1, 9, 15, tzinfo=timezone.utc) + timedelta(minutes=idx)
    return Candle(
        symbol=symbol,
        timestamp=ts,
        open=price,
        high=price,
        low=price,
        close=price,
        volume=100,
        source="unit",
        timeframe="1m",
    )


def test_strategy_initializes_defaults():
    strategy = EMACrossoverStrategy({"short_window": 3, "long_window": 5, "timeframe": "1m", "symbol_universe": ["TEST"]})

    assert strategy.short_ema is None
    assert strategy.long_ema is None
    assert strategy.signal() == "NONE"


def test_strategy_emits_buy_and_sell_on_crossovers():
    prices = [100, 99, 98, 99, 101, 103, 102, 100, 98, 97]
    strategy = EMACrossoverStrategy({"short_window": 3, "long_window": 5, "timeframe": "1m", "symbol_universe": ["TEST"]})

    signals = []
    for idx, price in enumerate(prices):
        strategy.update(_make_candle(price, idx=idx))
        signals.append(strategy.signal())

    assert signals[4] == "BUY"
    assert signals[8] == "SELL"
    assert signals[-1] == "NONE"


def test_strategy_returns_none_when_no_crossover():
    strategy = EMACrossoverStrategy({"short_window": 3, "long_window": 5, "timeframe": "1m", "symbol_universe": ["TEST"]})
    for idx, price in enumerate([100, 100, 100, 100, 100]):
        strategy.update(_make_candle(price, idx=idx))

    assert strategy.signal() == "NONE"


def test_ema_values_progress_over_time():
    prices = [100, 99, 98, 99, 101, 103, 102, 100, 98, 97]
    strategy = EMACrossoverStrategy({"short_window": 3, "long_window": 5, "timeframe": "1m", "symbol_universe": ["TEST"]})

    for idx, price in enumerate(prices):
        strategy.update(_make_candle(price, idx=idx))

    assert strategy.short_ema == pytest.approx(98.2168, rel=1e-4)
    assert strategy.long_ema == pytest.approx(98.9132, rel=1e-4)
    assert len(strategy.ema_history) == len(prices)

