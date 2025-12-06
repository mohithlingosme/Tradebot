"""Regression test: EMA crossover should trigger deterministic signals."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from trading_engine.phase4.models import Bar, SignalAction
from trading_engine.phase4.strategies.ema_crossover import EMACrossoverConfig, EMACrossoverStrategy


def _bar(price: float, idx: int) -> Bar:
    return Bar(
        symbol="AAPL",
        timestamp=datetime(2024, 1, 1, tzinfo=timezone.utc) + timedelta(minutes=idx),
        open=price,
        high=price,
        low=price,
        close=price,
        volume=1_000,
    )


def test_regression_triggers_buy_then_flat():
    strat = EMACrossoverStrategy(EMACrossoverConfig(short_period=3, long_period=5))
    signals = []
    for idx, price in enumerate([100, 101, 102, 103, 104, 103, 102]):
        payload = strat.on_bar(_bar(price, idx))
        if payload:
            signals.extend(signal.action for signal in payload)

    assert SignalAction.BUY in signals
    assert SignalAction.FLAT in signals
