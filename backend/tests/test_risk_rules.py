from decimal import Decimal

from backend.app.enums import OrderType, RiskAction, Side
from backend.app.models import RiskLimit
from backend.app.risk_engine import rules
from backend.app.risk_engine.types import OrderIntent, RiskSnapshot


def _snapshot(**kwargs) -> RiskSnapshot:
    base = dict(
        cash=Decimal("10000"),
        holdings_value=Decimal("0"),
        positions_value=Decimal("0"),
        gross_exposure=Decimal("0"),
        net_exposure=Decimal("0"),
        day_pnl=Decimal("0"),
        day_pnl_pct=Decimal("0"),
        open_orders_count=0,
        per_symbol_exposure={},
        per_symbol_qty={},
        last_price={},
    )
    base.update(kwargs)
    return RiskSnapshot(**base)


def _intent(**kwargs) -> OrderIntent:
    base = dict(
        symbol="AAPL",
        side=Side.BUY,
        qty=Decimal("10"),
        order_type=OrderType.MARKET,
        limit_price=None,
        current_price=Decimal("100"),
        product="MIS",
        strategy_id=None,
    )
    base.update(kwargs)
    return OrderIntent(**base)


def test_rule_kill_switch_blocks():
    snapshot = _snapshot()
    limits = RiskLimit(is_halted=True, halted_reason="manual halt")
    decision = rules.rule_kill_switch_if_halted(snapshot, limits)
    assert decision is not None
    assert decision.action == RiskAction.HALT_TRADING
    assert decision.reason_code == "TRADING_HALTED"


def test_cutoff_time_blocks_after_cutoff():
    snapshot = _snapshot()
    intent = _intent()
    limits = RiskLimit(cutoff_time="00:00", is_enabled=True)
    decision = rules.rule_cutoff_time(snapshot, limits, intent)
    assert decision is not None
    assert decision.action == RiskAction.REJECT
    assert decision.reason_code == "CUTOFF_TIME_BREACHED"


def test_max_gross_exposure_blocks_projected_breach():
    snapshot = _snapshot(gross_exposure=Decimal("100"), per_symbol_exposure={"AAPL": Decimal("60")})
    intent = _intent(limit_price=Decimal("10"))
    limits = RiskLimit(max_gross_exposure_inr=Decimal("150"))
    decision = rules.rule_max_gross_exposure(snapshot, limits, intent)
    assert decision is not None
    assert decision.reason_code == "MAX_GROSS_EXPOSURE_BREACHED"


def test_max_position_qty_blocks_large_buy():
    snapshot = _snapshot(per_symbol_qty={"AAPL": Decimal("0")})
    intent = _intent(qty=Decimal("5"))
    limits = RiskLimit(max_position_qty=1)
    decision = rules.rule_max_position_qty(snapshot, limits, intent)
    assert decision is not None
    assert decision.action == RiskAction.REJECT
    assert decision.reason_code == "MAX_POSITION_QTY_BREACHED"
