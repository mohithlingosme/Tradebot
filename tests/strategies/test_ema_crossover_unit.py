"""Unit tests for the EMA crossover strategy (legacy strategies package)."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from common.market_data import Candle
from strategies.ema_crossover.strategy import EMACrossoverStrategy


def _candle(price: float, idx: int = 0) -> Candle:
    ts = datetime(2024, 1, 1, 9, 15, tzinfo=timezone.utc) + timedelta(minutes=idx)
    return Candle(
        symbol="NIFTY",
        timestamp=ts,
        open=price,
        high=price + 1,
        low=price - 1,
        close=price,
        volume=1000,
        timeframe="5m",
    )


def test_strategy_emits_buy_and_sell_signals():
    strategy = EMACrossoverStrategy({"short_window": 3, "long_window": 5, "symbol_universe": ["NIFTY"]})
    prices = [100, 101, 102, 103, 104, 105, 104, 103, 102]
    signals = [strategy.on_bar(_candle(price, idx), strategy.state) for idx, price in enumerate(prices)]
    assert "BUY" in signals
    assert "SELL" in signals


def test_strategy_ignores_other_symbols():
    strategy = EMACrossoverStrategy({"symbol_universe": ["BANKNIFTY"]})
    signal = strategy.on_bar(_candle(100.0), strategy.state)
    assert signal == "HOLD"
