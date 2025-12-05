from __future__ import annotations

"""
Kite broker adapter.

The implementation keeps the hard requirements (risk checks, sizing) out of this
layer so individual brokers can be swapped without duplicating business logic.
"""

from datetime import datetime
import logging
from typing import Iterable, Optional

from .base_broker import Balance, BaseBroker, Order, OrderSide, OrderStatus, OrderType, Position

try:
    from kiteconnect import KiteConnect  # type: ignore
except ImportError:  # pragma: no cover - optional dependency installed in trading extras
    KiteConnect = None

logger = logging.getLogger(__name__)


class KiteBroker(BaseBroker):
    """Minimal adapter around the official KiteConnect SDK."""

    def __init__(
        self,
        api_key: str | None = None,
        access_token: str | None = None,
        exchange: str = "NSE",
        product: str = "MIS",
        variety: str = "regular",
    ):
        self.api_key = api_key
        self.access_token = access_token
        self.exchange = exchange
        self.product = product
        self.variety = variety
        self._client: Optional[KiteConnect] = None

    # ------------------------------------------------------------------ helpers
    def _ensure_client(self) -> KiteConnect:
        if KiteConnect is None:
            raise RuntimeError("kiteconnect package is not installed")
        if not self.api_key or not self.access_token:
            raise RuntimeError("Kite API key/access token are not configured")
        if not self._client:
            self._client = KiteConnect(api_key=self.api_key)
            self._client.set_access_token(self.access_token)
        return self._client

    def _fetch_order_payload(self, order_id: str) -> Optional[dict]:
        client = self._ensure_client()
        orders = client.orders()
        for payload in orders:
            if str(payload.get("order_id")) == str(order_id):
                return payload
        return None

    def _apply_broker_snapshot(self, order: Order, payload: Optional[dict]) -> None:
        if not payload:
            return
        status = payload.get("status", "").upper()
        order.status = OrderStatus(status) if status in OrderStatus.__members__ else order.status
        order.avg_fill_price = float(payload.get("average_price") or order.avg_fill_price or 0.0)
        order.filled_quantity = int(payload.get("filled_quantity") or order.filled_quantity)
        order.updated_at = datetime.utcnow()

    # ------------------------------------------------------------------ interface
    def place_order(self, order: Order) -> Order:
        client = self._ensure_client()
        order_type_map = {
            OrderType.MARKET: client.ORDER_TYPE_MARKET,
            OrderType.LIMIT: client.ORDER_TYPE_LIMIT,
            OrderType.STOP: client.ORDER_TYPE_SL,
            OrderType.STOP_LIMIT: client.ORDER_TYPE_SL,
        }
        transaction_type = (
            client.TRANSACTION_TYPE_BUY if order.side == OrderSide.BUY else client.TRANSACTION_TYPE_SELL
        )
        variety = getattr(client, f"VARIETY_{self.variety.upper()}", client.VARIETY_REGULAR)
        payload = client.place_order(
            variety=variety,
            exchange=self.exchange,
            tradingsymbol=order.symbol,
            transaction_type=transaction_type,
            quantity=order.quantity,
            order_type=order_type_map.get(order.order_type, client.ORDER_TYPE_MARKET),
            product=self.product,
            price=order.price or 0.0,
            validity=client.VALIDITY_DAY,
            trigger_price=order.price if order.order_type in {OrderType.STOP, OrderType.STOP_LIMIT} else 0.0,
        )
        order.external_id = payload.get("order_id")
        order.status = OrderStatus.NEW
        self._apply_broker_snapshot(order, self._fetch_order_payload(order.external_id))
        return order

    def cancel_order(self, order_id: str) -> bool:
        client = self._ensure_client()
        variety = getattr(client, f"VARIETY_{self.variety.upper()}", client.VARIETY_REGULAR)
        try:
            client.cancel_order(variety=variety, order_id=order_id)
            return True
        except Exception as exc:  # pragma: no cover - network side-effects
            logger.warning("Failed to cancel Kite order %s: %s", order_id, exc)
            return False

    def get_order_status(self, order_id: str) -> Optional[Order]:
        payload = self._fetch_order_payload(order_id)
        if not payload:
            return None
        order = Order(
            id=order_id,
            symbol=payload.get("tradingsymbol", ""),
            side=OrderSide(payload.get("transaction_type", "BUY")),
            quantity=int(payload.get("quantity", 0)),
            order_type=OrderType.MARKET,
            price=float(payload.get("price") or 0.0),
        )
        order.external_id = order_id
        self._apply_broker_snapshot(order, payload)
        return order

    def list_positions(self) -> Iterable[Position]:
        client = self._ensure_client()
        try:
            book = client.positions()
        except Exception as exc:  # pragma: no cover - network dependency
            logger.warning("Kite position snapshot failed: %s", exc)
            return []
        net_positions = book.get("net", [])
        mapped: list[Position] = []
        for p in net_positions:
            qty = int(p.get("quantity", 0))
            avg_price = float(p.get("average_price") or 0.0)
            pnl = float(p.get("pnl") or 0.0)
            mapped.append(
                Position(
                    symbol=p.get("tradingsymbol", ""),
                    quantity=qty,
                    avg_price=avg_price,
                    realized_pnl=pnl,
                    unrealized_pnl=float(p.get("unrealised", 0.0) or 0.0),
                )
            )
        return mapped

    def get_balance(self) -> Balance:
        client = self._ensure_client()
        margins = client.margins(segment="equity")
        available = margins.get("available", {}) if isinstance(margins, dict) else {}
        return Balance(
            available=float(available.get("cash", 0.0)),
            equity=float(margins.get("net", 0.0)),
            currency="INR",
        )
