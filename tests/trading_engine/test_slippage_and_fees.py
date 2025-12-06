"""Regression tests for backtester slippage/commission calculations."""

from __future__ import annotations

from datetime import datetime

from trading_engine.backtester import BacktestConfig, Backtester, BacktestMode


def _config():
    return BacktestConfig(
        start_date=datetime(2024, 1, 1),
        end_date=datetime(2024, 1, 10),
        initial_capital=100000,
        slippage=0.001,
        commission_per_trade=0.0005,
        mode=BacktestMode.SINGLE_RUN,
    )


def test_execute_trade_applies_slippage_and_commission():
    backtester = Backtester(_config())
    trade = backtester._execute_trade(
        signal="buy",
        symbol="AAPL",
        price=100.0,
        timestamp=datetime(2024, 1, 2),
        current_position=0,
        entry_price=0.0,
    )
    assert trade is not None
    assert trade.price > 100.0  # slippage applied
    assert trade.commission > 0


def test_sell_trade_using_slippage_discount():
    backtester = Backtester(_config())
    trade = backtester._execute_trade(
        signal="sell",
        symbol="AAPL",
        price=100.0,
        timestamp=datetime(2024, 1, 2),
        current_position=10,
        entry_price=99.0,
    )
    assert trade.price < 100.0
