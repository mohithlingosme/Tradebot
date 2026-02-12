import pytest
from decimal import Decimal
import datetime as dt

from backend.app.risk_engine import rules
from backend.app.risk_engine.types import OrderIntent, RiskSnapshot
from backend.app.models.risk_limit import RiskLimit
from backend.app.enums import Side, OrderType, RiskEventType


@pytest.fixture
def snapshot() -> RiskSnapshot:
    return RiskSnapshot(
        cash=Decimal("100000"),
        holdings_value=Decimal("0"),
        positions_value=Decimal("0"),
        gross_exposure=Decimal("0"),
        net_exposure=Decimal("0"),
        day_pnl=Decimal("0"),
        day_pnl_pct=Decimal("0"),
        open_orders_count=0,
        per_symbol_exposure={},
    )


@pytest.fixture
def limits() -> RiskLimit:
    return RiskLimit(
        daily_loss_inr=Decimal("1000"),
        daily_loss_pct=Decimal("10"),
        max_open_orders=10,
        cutoff_time="15:15",
        is_halted=False,
    )


@pytest.fixture
def order_intent() -> OrderIntent:
    return OrderIntent(
        symbol="RELIANCE",
        side=Side.BUY,
        qty=Decimal("10"),
        order_type=OrderType.LIMIT,
        limit_price=Decimal("2500"),
        product="CNC",
    )


def test_rule_kill_switch_if_halted(snapshot, limits):
    limits.is_halted = True
    limits.halted_reason = "Test halt"
    decision = rules.rule_kill_switch_if_halted(snapshot, limits)
    assert decision.action == RiskEventType.REJECT
    assert decision.reason_code == "TRADING_HALTED"


def test_rule_cutoff_time(snapshot, limits, order_intent):
    # Mocking time to be after cutoff
    kolkata_tz = dt.timezone(dt.timedelta(hours=5, minutes=30))
    cutoff = dt.datetime.now(kolkata_tz).replace(hour=16, minute=0)
    
    import datetime
    class PatchedDateTime(datetime.datetime):
        @classmethod
        def utcnow(cls):
            return cutoff.astimezone(dt.timezone.utc)
    
    rules.dt.datetime = PatchedDateTime

    decision = rules.rule_cutoff_time(snapshot, limits, order_intent)
    assert decision.action == RiskEventType.REJECT
    assert decision.reason_code == "CUTOFF_TIME_BREACHED"
    
    # Resetting datetime
    import datetime
    rules.dt.datetime = datetime.datetime


def test_rule_max_open_orders(snapshot, limits, order_intent):
    snapshot.open_orders_count = 10
    decision = rules.rule_max_open_orders(snapshot, limits, order_intent)
    assert decision.action == RiskEventType.REJECT
    assert decision.reason_code == "MAX_OPEN_ORDERS_BREACHED"


def test_rule_max_daily_loss_inr(snapshot, limits):
    snapshot.day_pnl = Decimal("-1001")
    decision = rules.rule_max_daily_loss_inr(snapshot, limits)
    assert decision.action == RiskEventType.HALT
    assert decision.reason_code == "MAX_DAILY_LOSS_INR_BREACHED"


def test_rule_max_daily_loss_pct(snapshot, limits):
    snapshot.day_pnl_pct = Decimal("-11")
    decision = rules.rule_max_daily_loss_pct(snapshot, limits)
    assert decision.action == RiskEventType.HALT
    assert decision.reason_code == "MAX_DAILY_LOSS_PCT_BREACHED"


def test_rule_price_sanity(order_intent):
    order_intent.limit_price = Decimal("-10")
    decision = rules.rule_price_sanity(order_intent)
    assert decision.action == RiskEventType.REJECT
    assert decision.reason_code == "INVALID_PRICE"
