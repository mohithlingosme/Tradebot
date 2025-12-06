"""Smoke tests for the backtester run loop."""

from __future__ import annotations

from datetime import datetime, timedelta

import pandas as pd

from trading_engine.backtester import BacktestConfig, Backtester
from trading_engine.strategy_manager import BaseStrategy


class TrendStrategy(BaseStrategy):
    def __init__(self):
        super().__init__({"name": "trend"})

    def analyze(self, data):
        price = data["close"]
        return {"signal": "buy" if price % 2 == 0 else "sell", "confidence": 0.7}


def _market_data():
    idx = pd.date_range(start=datetime(2024, 1, 1), periods=10, freq="D")
    return pd.DataFrame(
        {"open": range(10), "high": range(1, 11), "low": range(10), "close": range(10)},
        index=idx,
    )


def test_run_backtest_produces_result():
    config = BacktestConfig(
        start_date=datetime(2024, 1, 1),
        end_date=datetime(2024, 1, 10),
        initial_capital=100000,
    )
    backtester = Backtester(config)
    result = backtester.run_backtest(TrendStrategy(), _market_data())
    assert result.total_trades >= 0
    assert isinstance(result.total_return, float)
