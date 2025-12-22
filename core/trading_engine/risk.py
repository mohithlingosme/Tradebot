"""
Risk management layer for the Phase 4 engine.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .models import OrderRequest, OrderSide, PortfolioState, RiskDecision, RiskDecisionType


@dataclass
class RiskLimits:
    """Configurable risk limits."""

    max_position_pct: float = 0.1  # per-symbol notional / equity
    max_leverage: float = 2.0  # exposure / equity
    max_open_positions: int = 10
    max_daily_loss: float = 0.05
    max_order_notional: Optional[float] = None
    allow_partial: bool = True


class RiskManager:
    """Evaluates orders against configured limits."""

    def __init__(self, limits: Optional[RiskLimits] = None):
        self.limits = limits or RiskLimits()

    def evaluate(self, order: OrderRequest, portfolio: PortfolioState, market_price: float) -> RiskDecision:
        """
        Validate and optionally resize an order.

        Returns:
            RiskDecision describing whether to ALLOW, MODIFY, or REJECT the order.
        """
        equity = portfolio.equity
        if equity <= 0:
            return RiskDecision(RiskDecisionType.REJECT, None, reason="No equity available")

        if portfolio.daily_start_equity is None:
            portfolio.daily_start_equity = equity

        decision = self._check_daily_loss(portfolio)
        if decision:
            return decision

        modified = False
        notional = order.quantity * market_price
        if self.limits.max_order_notional and notional > self.limits.max_order_notional:
            if not self.limits.allow_partial:
                return RiskDecision(RiskDecisionType.REJECT, None, reason="Max order notional exceeded")
            scaled_qty = self.limits.max_order_notional / market_price
            if scaled_qty <= 0:
                return RiskDecision(RiskDecisionType.REJECT, None, reason="Order size reduced to zero")
            order = self._clone_with_quantity(order, scaled_qty)
            modified = True
            notional = order.quantity * market_price

        # Per-symbol sizing
        resized_order, symbol_reason = self._enforce_symbol_limit(order, portfolio, market_price)
        if resized_order is None:
            return RiskDecision(RiskDecisionType.REJECT, None, reason=symbol_reason)
        order = resized_order
        modified = modified or symbol_reason is not None
        notional = order.quantity * market_price

        # Portfolio-level leverage
        exposure_after = portfolio.exposure
        if order.side == OrderSide.BUY:
            exposure_after += notional
        else:
            exposure_after = max(0.0, exposure_after - notional)

        if exposure_after / equity > self.limits.max_leverage:
            if not self.limits.allow_partial:
                return RiskDecision(RiskDecisionType.REJECT, None, reason="Max leverage exceeded")
            allowed_exposure = self.limits.max_leverage * equity
            max_additional = max(0.0, allowed_exposure - portfolio.exposure)
            scaled_qty = max_additional / market_price
            if scaled_qty <= 0:
                return RiskDecision(RiskDecisionType.REJECT, None, reason="Leverage limit reached")
            order = self._clone_with_quantity(order, scaled_qty)
            modified = True
            notional = order.quantity * market_price

        # Open positions limit (only when increasing exposure in a new symbol)
        if order.symbol not in portfolio.positions and order.side == OrderSide.BUY:
            open_positions = len([p for p in portfolio.positions.values() if p.quantity != 0])
            if open_positions >= self.limits.max_open_positions:
                return RiskDecision(RiskDecisionType.REJECT, None, reason="Max open positions reached")

        if modified:
            return RiskDecision(RiskDecisionType.MODIFY, order, reason="Order resized for risk limits")
        return RiskDecision(RiskDecisionType.ALLOW, order)

    def _check_daily_loss(self, portfolio: PortfolioState) -> Optional[RiskDecision]:
        drawdown = portfolio.daily_pnl / portfolio.daily_start_equity if portfolio.daily_start_equity else 0.0
        if drawdown < -self.limits.max_daily_loss:
            return RiskDecision(RiskDecisionType.REJECT, None, reason="Daily loss limit reached")
        return None

    def _enforce_symbol_limit(
        self, order: OrderRequest, portfolio: PortfolioState, market_price: float
    ) -> tuple[Optional[OrderRequest], Optional[str]]:
        current = portfolio.positions.get(order.symbol)
        equity = portfolio.equity

        current_value = abs(current.market_value()) if current else 0.0
        # Directionally adjust for sell orders reducing exposure
        if order.side == OrderSide.SELL and current:
            reduced_value = max(0.0, current_value - order.quantity * market_price)
            if reduced_value / equity <= self.limits.max_position_pct:
                return order, None

        new_notional = current_value + (order.quantity * market_price if order.side == OrderSide.BUY else 0.0)
        if new_notional / equity <= self.limits.max_position_pct:
            return order, None

        if not self.limits.allow_partial:
            return None, "Max position size exceeded"

        allowed_notional = max(0.0, self.limits.max_position_pct * equity - current_value)
        scaled_qty = allowed_notional / market_price
        if scaled_qty <= 0:
            return None, "Position size limit reached"
        return self._clone_with_quantity(order, scaled_qty), "Order resized for position limit"

    @staticmethod
    def _clone_with_quantity(order: OrderRequest, quantity: float) -> OrderRequest:
        return OrderRequest(
            symbol=order.symbol,
            side=order.side,
            quantity=quantity,
            order_type=order.order_type,
            limit_price=order.limit_price,
            stop_loss=order.stop_loss,
            take_profit=order.take_profit,
            trailing_stop=order.trailing_stop,
            strategy_name=order.strategy_name,
            metadata=order.metadata.copy(),
        )
