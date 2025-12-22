from __future__ import annotations

"""Risk management layer (“The Shield”) enforcing capital protection rules."""

from dataclasses import dataclass, field, replace
from datetime import datetime, time, timezone
import logging
from typing import Any, Dict, List, Literal, Optional, Tuple
from zoneinfo import ZoneInfo

logger = logging.getLogger(__name__)

Side = Literal["BUY", "SELL"]
OrderType = Literal["MARKET", "LIMIT", "STOP", "STOP_LIMIT"]
ProductType = Literal["INTRADAY", "DELIVERY"]

TZ_ASIA_KOLKATA = ZoneInfo("Asia/Kolkata")


@dataclass(slots=True)
class OrderRequest:
    """Normalized order payload consumed by both legacy and new risk engines."""

    symbol: str
    side: Side
    qty: float
    price: Optional[float] = None
    order_type: OrderType = "MARKET"
    product_type: ProductType = "INTRADAY"
    ts: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    instrument_type: str = "EQUITY"
    stop_price: Optional[float] = None
    reduces_position: bool = False
    lot_size: int = 1
    option_type: Optional[str] = None
    meta: Dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class RiskContext:
    """Current account state required for risk decisions."""

    available_margin: Optional[float]
    day_pnl: Optional[float]
    positions: Dict[str, float] = field(default_factory=dict)
    last_price: Dict[str, float] = field(default_factory=dict)
    circuit_limits: Optional[Dict[str, Tuple[float, float]]] = None
    max_position_per_symbol: Optional[Dict[str, float]] = None
    max_daily_loss: float = 0.0
    trade_cutoff_time: time = time(15, 15)
    market_open_time: time = time(9, 15)
    market_close_time: time = time(15, 30)
    strict_circuit_check: bool = True


@dataclass(slots=True)
class RiskDecision:
    """Result of a risk evaluation."""

    approved: bool
    blocked: bool
    reasons: List[str]
    message: str
    adjusted_order: Optional[OrderRequest] = None


class RiskEngine:
    """Core rule engine for per-order risk evaluation."""

    def __init__(
        self,
        *,
        max_daily_loss: float,
        max_pos_default: float,
        trade_cutoff: time = time(15, 15),
        timezone: ZoneInfo = TZ_ASIA_KOLKATA,
        strict_circuit_check: bool = True,
    ) -> None:
        self.max_daily_loss = max_daily_loss
        self.max_pos_default = max_pos_default
        self.trade_cutoff = trade_cutoff
        self.timezone = timezone
        self.strict_circuit_check = strict_circuit_check

    def evaluate(self, order: OrderRequest, ctx: RiskContext) -> RiskDecision:
        ctx = self._hydrate_context(ctx)
        order = self._ensure_price(order, ctx)

        halted_decision = self._check_kill_switch(ctx)
        if halted_decision:
            return halted_decision

        time_decision = self._check_time_filters(order, ctx)
        if time_decision:
            return time_decision

        position_decision = self._check_position_limits(order, ctx)
        if position_decision:
            return position_decision

        sanity_decision = self._check_sanity(order, ctx)
        if sanity_decision:
            return sanity_decision

        return RiskDecision(
            approved=True,
            blocked=False,
            reasons=[],
            message="APPROVED",
        )

    def is_trading_halted(self, ctx: RiskContext) -> bool:
        ctx = self._hydrate_context(ctx)
        return ctx.day_pnl is not None and ctx.day_pnl <= -ctx.max_daily_loss

    # --- Private helpers -------------------------------------------------
    def _hydrate_context(self, ctx: RiskContext) -> RiskContext:
        hydrated = replace(ctx)
        hydrated.max_daily_loss = hydrated.max_daily_loss or self.max_daily_loss
        hydrated.trade_cutoff_time = hydrated.trade_cutoff_time or self.trade_cutoff
        hydrated.strict_circuit_check = hydrated.strict_circuit_check and self.strict_circuit_check
        if hydrated.max_position_per_symbol is None:
            hydrated.max_position_per_symbol = {}
        return hydrated

    def _ensure_price(self, order: OrderRequest, ctx: RiskContext) -> OrderRequest:
        if order.price is not None:
            return order
        price = ctx.last_price.get(order.symbol)
        if price is None:
            return order
        return replace(order, price=price, meta={**order.meta, "price_source": "last_price"})

    def _check_kill_switch(self, ctx: RiskContext) -> Optional[RiskDecision]:
        if self.is_trading_halted(ctx):
            logger.warning("Kill switch active: day_pnl=%s limit=%s", ctx.day_pnl, ctx.max_daily_loss)
            return RiskDecision(
                approved=False,
                blocked=True,
                reasons=["KILL_SWITCH_DAILY_LOSS"],
                message="Daily loss limit breached. Trading halted.",
            )
        return None

    def _check_time_filters(self, order: OrderRequest, ctx: RiskContext) -> Optional[RiskDecision]:
        local_ts = self._to_local(order.ts)
        local_time = local_ts.time()
        if local_time < ctx.market_open_time or local_time > ctx.market_close_time:
            return RiskDecision(
                approved=False,
                blocked=False,
                reasons=["OUTSIDE_MARKET_HOURS"],
                message="Order outside market hours.",
            )
        if local_time >= ctx.trade_cutoff_time:
            return RiskDecision(
                approved=False,
                blocked=False,
                reasons=["TIME_CUTOFF"],
                message="Trade cutoff reached for intraday trading.",
            )
        return None

    def _check_position_limits(self, order: OrderRequest, ctx: RiskContext) -> Optional[RiskDecision]:
        current = ctx.positions.get(order.symbol, 0.0)
        qty = order.qty
        if qty <= 0:
            return RiskDecision(
                approved=False,
                blocked=False,
                reasons=["INVALID_QTY"],
                message="Order quantity must be positive.",
            )
        new_position = current + qty if order.side == "BUY" else current - qty
        max_allowed = ctx.max_position_per_symbol.get(order.symbol, self.max_pos_default)
        if max_allowed is not None and abs(new_position) > max_allowed:
            return RiskDecision(
                approved=False,
                blocked=False,
                reasons=["POSITION_LIMIT_EXCEEDED"],
                message=f"Position limit exceeded for {order.symbol}. Current={current}, qty={qty}, max={max_allowed}",
            )
        return None

    def _check_sanity(self, order: OrderRequest, ctx: RiskContext) -> Optional[RiskDecision]:
        price = order.price
        if price is None or price <= 0:
            return RiskDecision(
                approved=False,
                blocked=False,
                reasons=["MISSING_RISK_INPUT", "MISSING_PRICE"],
                message="Unable to determine price for risk checks.",
            )
        if ctx.available_margin is None:
            return RiskDecision(
                approved=False,
                blocked=False,
                reasons=["MISSING_RISK_INPUT", "MISSING_MARGIN"],
                message="Margin information unavailable.",
            )
        notional = order.qty * price
        if notional > ctx.available_margin:
            return RiskDecision(
                approved=False,
                blocked=False,
                reasons=["INSUFFICIENT_MARGIN"],
                message="Order value exceeds available margin.",
            )

        limits = (ctx.circuit_limits or {}).get(order.symbol)
        if limits is None:
            if ctx.strict_circuit_check:
                return RiskDecision(
                    approved=False,
                    blocked=False,
                    reasons=["MISSING_RISK_INPUT", "MISSING_CIRCUIT_LIMITS"],
                    message="Circuit limits unavailable for symbol.",
                )
        else:
            lower, upper = limits
            if price < lower or price > upper:
                return RiskDecision(
                    approved=False,
                    blocked=False,
                    reasons=["CIRCUIT_LIMIT_BREACH"],
                    message=f"Price {price} breaks circuit limits ({lower}, {upper}).",
                )
        return None

    def _to_local(self, ts: datetime) -> datetime:
        if ts.tzinfo is None:
            return ts.replace(tzinfo=ZoneInfo("UTC")).astimezone(self.timezone)
        return ts.astimezone(self.timezone)
@dataclass(slots=True)
class AccountState:
    """Simplified account snapshot used by the legacy RiskManager."""

    equity: float
    todays_pnl: float
    open_positions_count: int
    available_margin: Optional[float] = None
    positions: Dict[str, float] = field(default_factory=dict)
    last_price: Dict[str, float] = field(default_factory=dict)
    circuit_limits: Optional[Dict[str, Tuple[float, float]]] = None


@dataclass(slots=True)
class RiskLimits:
    """Configurable guardrails expressed as percentages of equity/margin."""

    max_daily_loss_pct: float = 0.05
    max_open_positions: int = 10
    max_risk_per_trade_pct: float = 0.01
    max_margin_utilization_pct: float = 1.0


class MarginCalculator:
    """Basic margin helper that supports both equities and options."""

    def __init__(self, intraday_leverage: float = 5.0, carry_leverage: float = 1.0):
        self.intraday_leverage = max(intraday_leverage, 1.0)
        self.carry_leverage = max(carry_leverage, 1.0)

    def required_margin(self, order: OrderRequest) -> float:
        lot_size = max(1, order.lot_size)
        notional = max(0.0, (order.price or 0.0) * order.qty * lot_size)
        leverage = self.intraday_leverage if order.product_type == "INTRADAY" else self.carry_leverage
        margin = notional / max(leverage, 1e-9)
        if order.instrument_type.upper() in {"OPT", "OPTION"} and order.side == "SELL":
            # Premium writing uses additional cushion
            margin *= 1.5
        return margin


def position_size_for_risk(
    equity: float,
    max_risk_per_trade_pct: float,
    entry_price: float,
    stop_price: float,
    lot_size: int = 1,
) -> int:
    """Return the maximum quantity respecting risk-per-trade and lot sizing."""

    stop_distance = abs(entry_price - stop_price)
    if equity <= 0 or max_risk_per_trade_pct <= 0 or stop_distance <= 0:
        return 0
    risk_amount = equity * max_risk_per_trade_pct
    raw_qty = int(risk_amount // stop_distance)
    if raw_qty <= 0:
        return 0
    lot = max(1, lot_size)
    return (raw_qty // lot) * lot


class RiskManager:
    """
    Legacy RiskManager retained for strategies/tests that depend on the simple API.
    """

    def __init__(
        self,
        limits: Optional[RiskLimits] = None,
        margin_calculator: Optional[MarginCalculator] = None,
        timezone: ZoneInfo = TZ_ASIA_KOLKATA,
    ) -> None:
        self.limits = limits or RiskLimits()
        self.margin_calculator = margin_calculator or MarginCalculator()
        self.circuit_breaker_triggered = False
        self._timezone = timezone
        self._last_state: Optional[AccountState] = None

    def update_account_state(self, state: AccountState) -> None:
        self._last_state = state
        self._update_circuit_breaker(state)

    def validate_order(self, state: Optional[AccountState], order: OrderRequest) -> Tuple[bool, str]:
        snapshot = state or self._last_state
        if snapshot is None:
            return False, "Account state unavailable"
        self.update_account_state(snapshot)

        if self.circuit_breaker_triggered:
            return False, "Circuit breaker triggered: daily loss limit reached"

        if not self.can_open_new_position(snapshot, order):
            return False, "Max open positions reached"

        margin_ok, margin_reason = self._check_margin(snapshot, order)
        if not margin_ok:
            return False, margin_reason

        return True, "OK"

    def can_open_new_position(self, state: Optional[AccountState], order: Optional[OrderRequest] = None) -> bool:
        snapshot = state or self._last_state
        if snapshot is None:
            return False
        if order and order.reduces_position:
            return True
        return snapshot.open_positions_count < self.limits.max_open_positions

    # ------------------------------------------------------------------
    def _update_circuit_breaker(self, state: AccountState) -> None:
        threshold = max(0.0, state.equity * self.limits.max_daily_loss_pct)
        self.circuit_breaker_triggered = threshold > 0 and state.todays_pnl <= -threshold

    def _check_margin(self, state: AccountState, order: OrderRequest) -> Tuple[bool, str]:
        if state.available_margin is None:
            return False, "Insufficient margin information"
        required = self.margin_calculator.required_margin(order)
        allowed = state.available_margin * max(self.limits.max_margin_utilization_pct, 0)
        if required > allowed:
            return False, "Insufficient margin available"
        return True, "OK"
