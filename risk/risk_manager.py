from __future__ import annotations

"""Deterministic risk checks and position sizing helpers.

This module never submits orders. It only approves/rejects requests based on
configured limits and conservative margin/risk assumptions.
"""

from dataclasses import dataclass
from math import floor
from typing import Optional, Tuple


@dataclass
class RiskLimits:
    max_daily_loss_pct: float = 0.05  # 5% daily loss circuit breaker
    max_open_positions: int = 5
    max_risk_per_trade_pct: float = 0.01  # 1% of equity
    max_margin_utilization_pct: float = 1.0  # 100% of equity by default


@dataclass
class AccountState:
    equity: float
    todays_pnl: float
    open_positions_count: int
    available_margin: Optional[float] = None


@dataclass
class OrderRequest:
    symbol: str
    side: str  # "BUY" / "SELL"
    qty: int
    price: float
    product_type: str  # "INTRADAY", "CNC", "FUT", "OPT"
    instrument_type: str  # "EQUITY", "FUT", "OPT", "COMMODITY", etc.
    stop_price: Optional[float] = None
    strike: Optional[float] = None
    expiry: Optional[str] = None
    option_type: Optional[str] = None  # "CE" / "PE"
    lot_size: int = 1
    reduces_position: bool = False  # True when order is explicitly closing/reducing


class MarginCalculator:
    """
    Conservative margin estimator for F&O / equity trades.
    This is intentionally simplified: it should never underestimate margin.
    """

    def __init__(self, intraday_leverage: float = 5.0, carry_leverage: float = 1.0):
        self.intraday_leverage = intraday_leverage
        self.carry_leverage = carry_leverage

    def required_margin(self, order: OrderRequest) -> float:
        notional = order.price * order.qty * max(1, order.lot_size)

        if order.instrument_type.upper() in {"FUT", "OPT"}:
            leverage = self.intraday_leverage if order.product_type.upper() == "INTRADAY" else self.carry_leverage
            leverage = max(leverage, 1.0)
            margin = notional / leverage
            # Add a 10% buffer for option writing or slippage risk.
            if order.option_type and order.side.upper() == "SELL":
                margin *= 1.2
            else:
                margin *= 1.1
            return margin

        # For cash equities/ETFs assume full notional (no leverage).
        return notional


def position_size_for_risk(
    equity: float,
    max_risk_per_trade_pct: float,
    entry_price: float,
    stop_price: float,
    lot_size: int = 1,
) -> int:
    """
    Calculate the maximum quantity based on risk per trade.

    Rounds down to the nearest lot_size to avoid exceeding risk budgets.
    """
    if entry_price <= 0 or stop_price <= 0:
        return 0

    risk_amount = equity * max_risk_per_trade_pct
    per_unit_risk = abs(entry_price - stop_price)
    if per_unit_risk <= 0:
        return 0

    raw_qty = floor(risk_amount / per_unit_risk)
    if raw_qty <= 0:
        return 0

    # Round down to lot size
    lots = raw_qty // lot_size
    return int(lots * lot_size)


class RiskManager:
    """Validates orders against configured limits and margin assumptions."""

    def __init__(self, limits: RiskLimits, margin_calculator: Optional[MarginCalculator] = None):
        self.limits = limits
        self.margin_calculator = margin_calculator or MarginCalculator()
        self.circuit_breaker_triggered = False
        self._account_state: Optional[AccountState] = None

    def update_account_state(self, state: AccountState) -> None:
        """Update internal view of equity, PnL, and open positions."""
        self._account_state = state
        self.check_circuit_breaker(state)

    def check_circuit_breaker(self, state: AccountState) -> bool:
        """Return True if trading should be stopped due to daily loss breach."""
        max_loss_amount = state.equity * self.limits.max_daily_loss_pct
        if state.todays_pnl <= -max_loss_amount:
            self.circuit_breaker_triggered = True
            return True
        return False

    def can_open_new_position(self, state: AccountState, order: Optional[OrderRequest] = None) -> bool:
        """Check max open positions and circuit breaker."""
        if self.circuit_breaker_triggered or self.check_circuit_breaker(state):
            return False
        if state.open_positions_count >= self.limits.max_open_positions:
            if order and order.reduces_position:
                return True
            return False
        return True

    def max_allowed_risk_amount(self, state: AccountState) -> float:
        """Return max INR risk per trade, based on equity and limits."""
        return state.equity * self.limits.max_risk_per_trade_pct

    def _risk_amount_for_order(self, state: AccountState, order: OrderRequest) -> Tuple[float, Optional[float]]:
        max_risk_amount = self.max_allowed_risk_amount(state)
        if order.stop_price is None:
            # Without an explicit stop we cannot size precisely; treat risk as full price move.
            return max_risk_amount, None

        per_unit_risk = abs(order.price - order.stop_price)
        potential_risk = per_unit_risk * order.qty
        return max_risk_amount, potential_risk

    def validate_order(self, state: AccountState, order: OrderRequest) -> Tuple[bool, str]:
        """
        Validate an order against circuit breaker, position limits, risk per trade,
        and margin availability.
        """
        self.update_account_state(state)

        if self.circuit_breaker_triggered:
            return False, "Circuit breaker triggered: daily loss limit breached"

        if not self.can_open_new_position(state, order):
            return False, "Max open positions reached; cannot open new trades"

        # Risk-per-trade check
        max_risk_amount, potential_risk = self._risk_amount_for_order(state, order)
        if potential_risk is not None and potential_risk > max_risk_amount:
            return False, f"Risk per trade exceeds limit: {potential_risk:.2f} > {max_risk_amount:.2f}"

        # Margin check
        required_margin = self.margin_calculator.required_margin(order)
        available_margin = state.available_margin if state.available_margin is not None else state.equity
        available_cap = available_margin * self.limits.max_margin_utilization_pct
        if required_margin > available_cap:
            return False, f"Insufficient margin: required {required_margin:.2f}, available {available_cap:.2f}"

        return True, "Order within risk limits"

