"""Order gating tests for circuit breaker and risk rules."""

from __future__ import annotations

from risk.risk_manager import AccountState, OrderRequest, RiskLimits, RiskManager


def test_circuit_breaker_blocks_orders_after_loss():
    limits = RiskLimits(max_daily_loss_pct=0.05)
    manager = RiskManager(limits)
    state = AccountState(equity=100000, todays_pnl=-6000, open_positions_count=0)
    order = OrderRequest(
        symbol="AAPL",
        side="BUY",
        qty=10,
        price=100.0,
        product_type="INTRADAY",
        instrument_type="EQUITY",
        stop_price=95.0,
    )
    allowed, reason = manager.validate_order(state, order)
    assert allowed is False
    assert "circuit" in reason.lower()
