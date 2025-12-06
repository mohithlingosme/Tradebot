"""Tests that risk overrides behave as expected."""

from __future__ import annotations

from risk.risk_manager import AccountState, OrderRequest, RiskLimits, RiskManager


def test_validate_order_rejects_when_margin_missing():
    limits = RiskLimits(max_daily_loss_pct=0.05, max_open_positions=3, max_risk_per_trade_pct=0.01)
    manager = RiskManager(limits)
    state = AccountState(equity=10000, todays_pnl=0, open_positions_count=0, available_margin=5000)
    order = OrderRequest(
        symbol="AAPL",
        side="BUY",
        qty=200,
        price=200.0,
        product_type="INTRADAY",
        instrument_type="EQUITY",
        stop_price=190.0,
    )

    allowed, reason = manager.validate_order(state, order)
    assert allowed is False
    assert "margin" in reason.lower()


def test_reduce_position_allowed_when_limit_reached():
    limits = RiskLimits(max_open_positions=1)
    manager = RiskManager(limits)
    state = AccountState(equity=10000, todays_pnl=0, open_positions_count=1, available_margin=10000)
    order = OrderRequest(
        symbol="AAPL",
        side="SELL",
        qty=10,
        price=100.0,
        product_type="INTRADAY",
        instrument_type="EQUITY",
        reduces_position=True,
        stop_price=95.0,
    )
    allowed, reason = manager.validate_order(state, order)
    assert allowed is True
