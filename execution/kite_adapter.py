from __future__ import annotations

"""
Stub adapter for Zerodha Kite (or similar) broker.

This adapter mirrors the BaseBroker interface; actual API calls should be
implemented with the broker SDK, ensuring no risk logic is embedded here.
"""

from typing import Iterable, Optional

from .base_broker import Balance, BaseBroker, Order, OrderSide, OrderStatus, Position


class KiteBroker(BaseBroker):
    """Placeholder Kite adapter; extend with real SDK calls."""

    def __init__(self, api_key: str | None = None, access_token: str | None = None):
        self.api_key = api_key
        self.access_token = access_token

    def place_order(self, order: Order) -> Order:
        # TODO: Wire to Kite order placement; return updated Order with external_id/status.
        order.status = OrderStatus.REJECTED
        order.external_id = None
        return order

    def cancel_order(self, order_id: str) -> bool:
        # TODO: Implement broker-side cancel
        return False

    def get_order_status(self, order_id: str) -> Optional[Order]:
        # TODO: Fetch from broker
        return None

    def list_positions(self) -> Iterable[Position]:
        # TODO: Map broker positions to Position dataclass
        return []

    def get_balance(self) -> Balance:
        # TODO: Pull funds/equity snapshot from broker
        return Balance(available=0.0, equity=0.0)

