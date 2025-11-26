from __future__ import annotations

"""In-memory mock broker for tests and dev."""

from datetime import datetime
from typing import Dict, Iterable, Optional

from .base_broker import Balance, BaseBroker, Order, OrderSide, OrderStatus, Position


class MockedBroker(BaseBroker):
    """Immediately fills market orders; no external side effects."""

    def __init__(self, starting_cash: float = 100_000.0):
        self._orders: Dict[str, Order] = {}
        self._positions: Dict[str, Position] = {}
        self._cash = starting_cash
        self._equity = starting_cash
        self._counter = 0

    def _next_id(self) -> str:
        self._counter += 1
        return f"MOCK-{self._counter}"

    def _update_position(self, order: Order) -> None:
        qty_delta = order.quantity if order.side == OrderSide.BUY else -order.quantity
        if order.symbol not in self._positions:
            self._positions[order.symbol] = Position(symbol=order.symbol, quantity=0, avg_price=order.avg_fill_price or order.price or 0.0)
        pos = self._positions[order.symbol]
        if qty_delta > 0:
            total_cost = pos.avg_price * pos.quantity + (order.avg_fill_price or 0.0) * qty_delta
            pos.quantity += qty_delta
            if pos.quantity > 0:
                pos.avg_price = total_cost / pos.quantity
        else:
            close_qty = min(pos.quantity, abs(qty_delta))
            pnl = (order.avg_fill_price or 0.0 - pos.avg_price) * close_qty
            pos.realized_pnl += pnl
            pos.quantity += qty_delta
            if pos.quantity == 0:
                pos.avg_price = 0.0

    def place_order(self, order: Order) -> Order:
        order.id = order.id or self._next_id()
        order.created_at = datetime.utcnow()
        order.updated_at = order.created_at

        # For mock, fill immediately at provided price (or 0 if missing)
        fill_price = float(order.price or 0.0)
        order.avg_fill_price = fill_price
        order.filled_quantity = order.quantity
        order.status = OrderStatus.FILLED
        self._orders[order.id] = order

        # Adjust cash and positions
        notional = fill_price * order.quantity
        if order.side == OrderSide.BUY:
            self._cash -= notional
        else:
            self._cash += notional
        self._equity = self._cash  # simplistic; ignore unrealized
        self._update_position(order)
        return order

    def cancel_order(self, order_id: str) -> bool:
        if order_id not in self._orders:
            return False
        order = self._orders[order_id]
        if order.status in {OrderStatus.FILLED, OrderStatus.CANCELLED, OrderStatus.REJECTED}:
            return False
        order.status = OrderStatus.CANCELLED
        order.updated_at = datetime.utcnow()
        return True

    def get_order_status(self, order_id: str) -> Optional[Order]:
        return self._orders.get(order_id)

    def list_positions(self) -> Iterable[Position]:
        return list(self._positions.values())

    def get_balance(self) -> Balance:
        return Balance(available=self._cash, equity=self._equity)

