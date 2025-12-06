"""Exposure limit tests for the risk manager."""

from __future__ import annotations

from risk.risk_manager import AccountState, OrderRequest, RiskLimits, RiskManager, position_size_for_risk


def test_position_size_for_risk_respects_lot_size():
    qty = position_size_for_risk(
        equity=100000,
        max_risk_per_trade_pct=0.01,
        entry_price=100.0,
        stop_price=95.0,
        lot_size=25,
    )
    assert qty % 25 == 0


def test_can_open_new_position_honours_open_position_limit():
    limits = RiskLimits(max_open_positions=1)
    manager = RiskManager(limits)
    full_state = AccountState(equity=100000, todays_pnl=0, open_positions_count=1)
    assert manager.can_open_new_position(full_state) is False
    reducing_order = OrderRequest(
        symbol="AAPL",
        side="SELL",
        qty=1,
        price=100.0,
        product_type="INTRADAY",
        instrument_type="EQUITY",
        reduces_position=True,
    )
    assert manager.can_open_new_position(full_state, reducing_order) is True
