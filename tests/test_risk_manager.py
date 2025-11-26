import pytest

from risk.risk_manager import (
    AccountState,
    MarginCalculator,
    OrderRequest,
    RiskLimits,
    RiskManager,
    position_size_for_risk,
)


class StubMargin(MarginCalculator):
    def __init__(self, required: float):
        super().__init__()
        self._required = required

    def required_margin(self, order: OrderRequest) -> float:  # type: ignore[override]
        return self._required


def test_circuit_breaker_triggers_and_rejects():
    limits = RiskLimits(max_daily_loss_pct=0.05)
    rm = RiskManager(limits, margin_calculator=StubMargin(0))
    state = AccountState(equity=100_000, todays_pnl=-6_000, open_positions_count=0, available_margin=100_000)
    order = OrderRequest(
        symbol="TEST",
        side="BUY",
        qty=1,
        price=100,
        product_type="INTRADAY",
        instrument_type="EQUITY",
        stop_price=95,
    )

    ok, reason = rm.validate_order(state, order)
    assert not ok
    assert "Circuit breaker" in reason


def test_max_open_positions_rejects_new_open():
    limits = RiskLimits(max_open_positions=5)
    rm = RiskManager(limits, margin_calculator=StubMargin(0))
    state = AccountState(equity=100_000, todays_pnl=0, open_positions_count=5, available_margin=100_000)
    order_open = OrderRequest(
        symbol="TEST",
        side="BUY",
        qty=1,
        price=100,
        product_type="INTRADAY",
        instrument_type="EQUITY",
        stop_price=95,
    )
    ok_open, _ = rm.validate_order(state, order_open)
    assert not ok_open

    order_close = OrderRequest(
        symbol="TEST",
        side="SELL",
        qty=1,
        price=100,
        product_type="INTRADAY",
        instrument_type="EQUITY",
        reduces_position=True,
        stop_price=95,
    )
    ok_close, _ = rm.validate_order(state, order_close)
    assert ok_close


def test_position_size_for_risk_calculates_expected():
    qty = position_size_for_risk(
        equity=100_000,
        max_risk_per_trade_pct=0.01,
        entry_price=100,
        stop_price=95,
        lot_size=1,
    )
    assert qty == 200

    qty_lots = position_size_for_risk(
        equity=100_000,
        max_risk_per_trade_pct=0.01,
        entry_price=100,
        stop_price=95,
        lot_size=50,
    )
    assert qty_lots == 200 // 50 * 50  # floored to lot size


def test_margin_rejects_when_required_exceeds_available():
    limits = RiskLimits(max_margin_utilization_pct=1.0)
    rm = RiskManager(limits, margin_calculator=StubMargin(200_000))
    state = AccountState(equity=100_000, todays_pnl=0, open_positions_count=0, available_margin=50_000)
    order = OrderRequest(
        symbol="TEST",
        side="BUY",
        qty=10,
        price=100,
        product_type="INTRADAY",
        instrument_type="EQUITY",
        stop_price=95,
    )

    ok, reason = rm.validate_order(state, order)
    assert not ok
    assert "Insufficient margin" in reason

    rm_ok = RiskManager(limits, margin_calculator=StubMargin(10_000))
    ok, reason = rm_ok.validate_order(state, order)
    assert ok, reason

