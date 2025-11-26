from risk.risk_manager import (
    AccountState,
    MarginCalculator,
    OrderRequest,
    RiskLimits,
    RiskManager,
    position_size_for_risk,
)


def _order(**kwargs) -> OrderRequest:
    defaults = dict(
        symbol="TEST",
        side="BUY",
        qty=10,
        price=100.0,
        product_type="INTRADAY",
        instrument_type="EQUITY",
        stop_price=99.0,
        lot_size=1,
        reduces_position=False,
    )
    defaults.update(kwargs)
    return OrderRequest(**defaults)


def test_daily_loss_circuit_breaker_blocks_orders():
    limits = RiskLimits(max_daily_loss_pct=0.05)
    rm = RiskManager(limits)

    ok_state = AccountState(equity=100_000, todays_pnl=-4_000, open_positions_count=0)
    rm.update_account_state(ok_state)
    allowed, _ = rm.validate_order(ok_state, _order())
    assert allowed

    hit_state = AccountState(equity=100_000, todays_pnl=-6_000, open_positions_count=0)
    allowed, reason = rm.validate_order(hit_state, _order())
    assert not allowed
    assert "Circuit breaker" in reason


def test_max_open_positions_enforced():
    limits = RiskLimits(max_open_positions=3)
    rm = RiskManager(limits)

    state_full = AccountState(equity=50_000, todays_pnl=0, open_positions_count=3)
    allowed, reason = rm.validate_order(state_full, _order(reduces_position=False))
    assert not allowed
    assert "Max open positions" in reason

    state_room = AccountState(equity=50_000, todays_pnl=0, open_positions_count=2)
    allowed, _ = rm.validate_order(state_room, _order())
    assert allowed


def test_position_size_for_risk_respects_lot_size():
    qty = position_size_for_risk(
        equity=100_000,
        max_risk_per_trade_pct=0.01,
        entry_price=100.0,
        stop_price=95.0,
        lot_size=10,
    )
    # risk amount = 1000; per-unit risk = 5; raw qty=200; rounded to lot_size=10
    assert qty == 200


def test_margin_check_blocks_when_insufficient():
    class TinyMargin(MarginCalculator):
        def required_margin(self, order):  # type: ignore[override]
            return 1_000_000.0

    class LowMargin(MarginCalculator):
        def required_margin(self, order):  # type: ignore[override]
            return 1_000.0

    limits = RiskLimits(max_margin_utilization_pct=1.0)

    state = AccountState(equity=10_000, todays_pnl=0, open_positions_count=0, available_margin=5_000)

    rm_block = RiskManager(limits, margin_calculator=TinyMargin())
    allowed, reason = rm_block.validate_order(state, _order())
    assert not allowed
    assert "Insufficient margin" in reason

    rm_ok = RiskManager(limits, margin_calculator=LowMargin())
    allowed, _ = rm_ok.validate_order(state, _order())
    assert allowed
