"""
Paper trading execution and MTM portfolio tracking.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from .models import (
    Bar,
    OrderFill,
    OrderRequest,
    OrderSide,
    OrderStatus,
    OrderType,
    PortfolioPosition,
    PortfolioState,
)


@dataclass
class ExecutionLog:
    orders: List[OrderFill] = field(default_factory=list)
    trades: List[OrderFill] = field(default_factory=list)


class PaperTradingEngine:
    """Simulated execution venue with stop-loss / take-profit handling."""

    def __init__(self, portfolio: Optional[PortfolioState] = None, slippage_bps: float = 1.0, commission_rate: float = 0.0):
        self.portfolio = portfolio or PortfolioState(cash=100_000.0)
        if self.portfolio.daily_start_equity is None:
            self.portfolio.daily_start_equity = self.portfolio.equity
        self.slippage_bps = slippage_bps
        self.commission_rate = commission_rate
        self.logs = ExecutionLog()

    def update_mark_to_market(self, bar: Bar) -> List[OrderFill]:
        """Mark positions to the latest price and trigger SL/TP."""
        exits: List[OrderFill] = []
        position = self.portfolio.positions.get(bar.symbol)
        if not position or position.quantity == 0:
            return exits

        position.update_price(bar.close)
        triggered_fill = self._check_exit_levels(position, bar)
        if triggered_fill:
            exits.append(triggered_fill)
        return exits

    def execute_order(self, order: OrderRequest, bar: Bar) -> OrderFill:
        """Fill an order on the given bar."""
        fill_price = self._determine_fill_price(order, bar)
        position = self.portfolio.positions.get(order.symbol)
        if position is None:
            position = PortfolioPosition(symbol=order.symbol, last_price=fill_price)
            self.portfolio.positions[order.symbol] = position

        if order.side == OrderSide.SELL and position.quantity <= 0:
            return OrderFill(order=order, filled_quantity=0.0, fill_price=fill_price, status=OrderStatus.REJECTED, reason="No position to sell")

        filled_qty, pnl = self._apply_fill(position, order, fill_price)

        if order.side == OrderSide.BUY and filled_qty > 0:
            position.stop_loss = order.stop_loss or position.stop_loss
            position.take_profit = order.take_profit or position.take_profit
            position.trailing_stop = order.trailing_stop or position.trailing_stop
            position.peak_price = position.peak_price or fill_price
        status = OrderStatus.FILLED if filled_qty == order.quantity else OrderStatus.PARTIALLY_FILLED
        fill = OrderFill(order=order, filled_quantity=filled_qty, fill_price=fill_price, status=status, pnl=pnl)
        self.logs.orders.append(fill)
        if filled_qty > 0:
            self.logs.trades.append(fill)
        return fill

    def _apply_fill(self, position: PortfolioPosition, order: OrderRequest, fill_price: float) -> tuple[float, float]:
        """Apply fill to portfolio and return (filled_qty, realized_pnl)."""
        qty = min(order.quantity, position.quantity) if order.side == OrderSide.SELL else order.quantity
        if qty <= 0:
            return 0.0, 0.0

        commission = fill_price * qty * self.commission_rate
        realized = 0.0

        if order.side == OrderSide.BUY:
            total_cost = position.average_price * position.quantity + fill_price * qty
            position.quantity += qty
            position.average_price = total_cost / position.quantity if position.quantity else fill_price
            position.entry_time = position.entry_time or order.created_at
            self.portfolio.cash -= (fill_price * qty) + commission
        else:
            realized = (fill_price - position.average_price) * qty
            position.quantity -= qty
            position.realized_pnl += realized
            self.portfolio.realized_pnl += realized
            self.portfolio.cash += (fill_price * qty) - commission
            if position.quantity == 0:
                position.average_price = 0.0
                position.stop_loss = None
                position.take_profit = None
                position.trailing_stop = None
                position.peak_price = None
                position.entry_time = None

        position.update_price(fill_price)
        return qty, realized

    def _determine_fill_price(self, order: OrderRequest, bar: Bar) -> float:
        base_price = order.limit_price if order.limit_price is not None else bar.close
        slip = (self.slippage_bps / 10_000) * base_price
        if order.side == OrderSide.BUY:
            return base_price + slip
        return base_price - slip

    def _check_exit_levels(self, position: PortfolioPosition, bar: Bar) -> Optional[OrderFill]:
        """Trigger SL/TP/trailing exits if price crosses thresholds."""
        exit_price = None
        reason = None

        if position.quantity <= 0:
            return None

        if position.stop_loss is not None and bar.low <= position.stop_loss:
            exit_price = position.stop_loss
            reason = "stop_loss"
        if position.take_profit is not None and bar.high >= position.take_profit:
            exit_price = exit_price or position.take_profit
            reason = reason or "take_profit"

        if position.trailing_stop is not None and position.peak_price is not None:
            trail_price = position.peak_price - position.trailing_stop
            if bar.low <= trail_price:
                exit_price = exit_price or trail_price
                reason = reason or "trailing_stop"

        if exit_price is None:
            return None

        order = OrderRequest(
            symbol=position.symbol,
            side=OrderSide.SELL,
            quantity=position.quantity,
            order_type=OrderType.MARKET,
            limit_price=exit_price,
            metadata={"reason": reason},
        )
        fill = self.execute_order(order, bar)
        fill.reason = reason
        return fill
