"""Tests for the mean reversion variant of the Bollinger strategy."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from trading_engine.phase4.models import Bar
from trading_engine.phase4.strategies.bollinger import BollingerBandsStrategy, BollingerConfig


def _bar(price: float, idx: int) -> Bar:
    return Bar(
        symbol="AAPL",
        timestamp=datetime(2024, 1, 1, tzinfo=timezone.utc) + timedelta(minutes=idx),
        open=price,
        high=price + 1,
        low=price - 1,
        close=price,
        volume=1_000,
    )


def test_mean_reversion_enters_and_exits():
    strat = BollingerBandsStrategy(BollingerConfig(period=5, num_std=1.0, mode="mean_reversion"))
    prices = [100, 100, 100, 100, 95, 90, 100, 105]
    signals = []
    for idx, price in enumerate(prices):
        payload = strat.on_bar(_bar(price, idx))
        if payload:
            signals.extend(signal.action.value for signal in payload)

    assert "buy" in signals
    assert "flat" in signals
