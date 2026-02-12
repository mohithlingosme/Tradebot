import datetime as dt
from decimal import Decimal
from typing import Optional

from backend.app.enums import OrderType, ProductType, RiskAction, Side
from backend.app.models import RiskLimit
from backend.app.risk_engine.types import OrderIntent, RiskDecision, RiskSnapshot

IST = dt.timezone(dt.timedelta(hours=5, minutes=30))
ZERO = Decimal("0")


def _signed_order_qty(order_intent: OrderIntent) -> Decimal:
    qty = Decimal(order_intent.qty)
    return qty if order_intent.side == Side.BUY else -qty


def _order_price(order_intent: OrderIntent, snapshot: RiskSnapshot) -> Decimal:
    if order_intent.order_type == OrderType.LIMIT and order_intent.limit_price is not None:
        return Decimal(order_intent.limit_price)
    if order_intent.current_price is not None:
        return Decimal(order_intent.current_price)
    return Decimal(snapshot.last_price.get(order_intent.symbol, ZERO))


def rule_kill_switch_if_halted(snapshot: RiskSnapshot, limits: RiskLimit) -> Optional[RiskDecision]:
    if limits.is_halted:
        return RiskDecision(
            action=RiskAction.HALT_TRADING,
            reason_code="TRADING_HALTED",
            message=f"Trading is halted. Reason: {limits.halted_reason or 'manual halt'}",
            breached_limits=["is_halted"],
        )
    return None


def rule_cutoff_time(snapshot: RiskSnapshot, limits: RiskLimit, order_intent: OrderIntent) -> Optional[RiskDecision]:
    if not limits.cutoff_time:
        return None

    cutoff_time = dt.datetime.strptime(limits.cutoff_time, "%H:%M").time()
    now_kolkata = dt.datetime.now(tz=IST).time()

    if now_kolkata > cutoff_time:
        return RiskDecision(
            action=RiskAction.REJECT,
            reason_code="CUTOFF_TIME_BREACHED",
            message=f"Order rejected after cutoff time {limits.cutoff_time} IST.",
            breached_limits=["cutoff_time"],
        )
    return None


def rule_max_open_orders(snapshot: RiskSnapshot, limits: RiskLimit, order_intent: OrderIntent) -> Optional[RiskDecision]:
    if limits.max_open_orders is not None and snapshot.open_orders_count >= limits.max_open_orders:
        return RiskDecision(
            action=RiskAction.REJECT,
            reason_code="MAX_OPEN_ORDERS_BREACHED",
            message=f"Exceeded max open orders ({limits.max_open_orders}).",
            breached_limits=["max_open_orders"],
        )
    return None


def rule_max_daily_loss_inr(snapshot: RiskSnapshot, limits: RiskLimit) -> Optional[RiskDecision]:
    if limits.daily_loss_inr is not None and snapshot.day_pnl < -Decimal(limits.daily_loss_inr):
        return RiskDecision(
            action=RiskAction.HALT_TRADING,
            reason_code="MAX_DAILY_LOSS_INR_BREACHED",
            message=f"Max daily loss of {limits.daily_loss_inr} INR breached. Current PNL: {snapshot.day_pnl}",
            breached_limits=["daily_loss_inr"],
        )
    return None


def rule_max_daily_loss_pct(snapshot: RiskSnapshot, limits: RiskLimit) -> Optional[RiskDecision]:
    if limits.daily_loss_pct is not None and limits.daily_loss_pct > 0 and snapshot.day_pnl_pct < -Decimal(limits.daily_loss_pct):
        return RiskDecision(
            action=RiskAction.HALT_TRADING,
            reason_code="MAX_DAILY_LOSS_PCT_BREACHED",
            message=f"Max daily loss of {limits.daily_loss_pct}% breached. Current PNL: {snapshot.day_pnl_pct}%",
            breached_limits=["daily_loss_pct"],
        )
    return None


def rule_max_position_qty(snapshot: RiskSnapshot, limits: RiskLimit, order_intent: OrderIntent) -> Optional[RiskDecision]:
    if limits.max_position_qty is None:
        return None

    current_qty = snapshot.per_symbol_qty.get(order_intent.symbol, ZERO)
    projected_qty = current_qty + _signed_order_qty(order_intent)
    if abs(projected_qty) > Decimal(limits.max_position_qty):
        return RiskDecision(
            action=RiskAction.REJECT,
            reason_code="MAX_POSITION_QTY_BREACHED",
            message=f"Projected position qty {projected_qty} exceeds limit {limits.max_position_qty} for {order_intent.symbol}.",
            breached_limits=["max_position_qty"],
        )
    return None


def rule_max_position_value(snapshot: RiskSnapshot, limits: RiskLimit, order_intent: OrderIntent) -> Optional[RiskDecision]:
    if limits.max_position_value_inr is None:
        return None

    price = _order_price(order_intent, snapshot)
    order_exposure = _signed_order_qty(order_intent) * price
    current_exposure = snapshot.per_symbol_exposure.get(order_intent.symbol, ZERO)
    projected_exposure = current_exposure + order_exposure
    if abs(projected_exposure) > Decimal(limits.max_position_value_inr):
        return RiskDecision(
            action=RiskAction.REJECT,
            reason_code="MAX_POSITION_VALUE_BREACHED",
            message=f"Projected exposure {projected_exposure} exceeds limit {limits.max_position_value_inr} for {order_intent.symbol}.",
            breached_limits=["max_position_value_inr"],
        )
    return None


def rule_max_gross_exposure(snapshot: RiskSnapshot, limits: RiskLimit, order_intent: OrderIntent) -> Optional[RiskDecision]:
    if limits.max_gross_exposure_inr is None:
        return None

    price = _order_price(order_intent, snapshot)
    order_exposure = _signed_order_qty(order_intent) * price
    current_exposure = snapshot.per_symbol_exposure.get(order_intent.symbol, ZERO)
    projected_symbol_exposure = current_exposure + order_exposure

    projected_gross = snapshot.gross_exposure - abs(current_exposure) + abs(projected_symbol_exposure)

    if projected_gross > Decimal(limits.max_gross_exposure_inr):
        return RiskDecision(
            action=RiskAction.REJECT,
            reason_code="MAX_GROSS_EXPOSURE_BREACHED",
            message=f"Projected gross exposure {projected_gross} exceeds limit {limits.max_gross_exposure_inr}.",
            breached_limits=["max_gross_exposure_inr"],
        )
    return None


def rule_max_net_exposure(snapshot: RiskSnapshot, limits: RiskLimit, order_intent: OrderIntent) -> Optional[RiskDecision]:
    if limits.max_net_exposure_inr is None:
        return None

    price = _order_price(order_intent, snapshot)
    order_exposure = _signed_order_qty(order_intent) * price
    projected_net = snapshot.net_exposure + order_exposure
    if abs(projected_net) > Decimal(limits.max_net_exposure_inr):
        return RiskDecision(
            action=RiskAction.REJECT,
            reason_code="MAX_NET_EXPOSURE_BREACHED",
            message=f"Projected net exposure {projected_net} exceeds limit {limits.max_net_exposure_inr}.",
            breached_limits=["max_net_exposure_inr"],
        )
    return None


def rule_cash_check(snapshot: RiskSnapshot, limits: RiskLimit, order_intent: OrderIntent) -> Optional[RiskDecision]:
    price = _order_price(order_intent, snapshot)
    if price <= 0:
        return RiskDecision(
            action=RiskAction.REJECT,
            reason_code="PRICE_MISSING",
            message="Price unavailable for order valuation.",
            breached_limits=["pricing"],
        )

    order_value = price * Decimal(order_intent.qty)
    product_value = order_intent.product.value if isinstance(order_intent.product, ProductType) else str(order_intent.product)
    if product_value.upper() == ProductType.CNC.value and order_intent.side == Side.BUY and order_value > snapshot.cash:
        return RiskDecision(
            action=RiskAction.REJECT,
            reason_code="INSUFFICIENT_CASH",
            message="Insufficient cash for CNC buy order.",
            breached_limits=["cash"],
        )
    return None


def rule_price_sanity(order_intent: OrderIntent) -> Optional[RiskDecision]:
    if order_intent.limit_price is not None and Decimal(order_intent.limit_price) <= 0:
        return RiskDecision(
            action=RiskAction.REJECT,
            reason_code="INVALID_PRICE",
            message="Limit price must be positive.",
            breached_limits=["price"],
        )
    return None
