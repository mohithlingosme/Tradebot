from enum import Enum
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Optional
import uuid
import logging

logger = logging.getLogger(__name__)


class OrderSide(Enum):
    BUY = "BUY"
    SELL = "SELL"


class OrderType(Enum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    SL = "SL"  # Stop Loss


class OrderStatus(Enum):
    PENDING = "PENDING"
    FILLED = "FILLED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"


@dataclass
class Order:
    order_id: str
    symbol: str
    qty: int
    side: OrderSide
    order_type: OrderType
    price: Optional[float] = None
    status: OrderStatus = OrderStatus.PENDING
    timestamp: datetime = None
    fill_price: Optional[float] = None
    slippage: Optional[float] = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


class ExecutionEngine:
    """
    Execution Engine for FINBOT trading system.
    Handles order placement, modification, and tracking.
    Supports both Live Trading (via broker API) and Paper Trading (simulation).
    """

    def __init__(self, broker_adapter=None, paper_trading: bool = True):
        """
        Initialize the ExecutionEngine.

        Args:
            broker_adapter: Broker API adapter for live trading
            paper_trading: If True, simulate trades without real broker
        """
        self.broker_adapter = broker_adapter
        self.paper_trading = paper_trading
        self.orders: Dict[str, Order] = {}
        self.positions: Dict[str, int] = {}

    def place_order(self, symbol: str, qty: int, side: OrderSide, order_type: OrderType, price: float = None) -> str:
        """
        Place a new order.

        Args:
            symbol: Ticker symbol
            qty: Quantity
            side: BUY or SELL
            order_type: MARKET, LIMIT, or SL
            price: Limit price (required for LIMIT/SL orders)

        Returns:
            order_id: Unique order identifier
        """
        order_id = str(uuid.uuid4())

        order = Order(
            order_id=order_id,
            symbol=symbol,
            qty=qty,
            side=side,
            order_type=order_type,
            price=price
        )

        self.orders[order_id] = order

        if self.paper_trading:
            # Simulate immediate fill for paper trading
            fill_price = self._simulate_fill_price(order)
            self._on_fill(order_id, fill_price, qty)
        else:
            # In live trading, this would send to broker
            # For now, we'll assume immediate fill for simplicity
            if self.broker_adapter:
                # broker_adapter.place_order(order)
                pass
            else:
                logger.warning("Live trading enabled but no broker adapter provided")

        return order_id

    def cancel_order(self, order_id: str) -> bool:
        """
        Cancel a pending order.

        Args:
            order_id: Order to cancel

        Returns:
            True if cancelled, False otherwise
        """
        if order_id in self.orders:
            order = self.orders[order_id]
            if order.status == OrderStatus.PENDING:
                order.status = OrderStatus.CANCELLED
                logger.info(f"Order {order_id} cancelled")
                return True
        return False

    def modify_order(self, order_id: str, new_price: float) -> bool:
        """
        Modify the price of a pending order.

        Args:
            order_id: Order to modify
            new_price: New limit price

        Returns:
            True if modified, False otherwise
        """
        if order_id in self.orders:
            order = self.orders[order_id]
            if order.status == OrderStatus.PENDING and order.order_type in [OrderType.LIMIT, OrderType.SL]:
                order.price = new_price
                logger.info(f"Order {order_id} modified: new price {new_price}")
                return True
        return False

    def get_order(self, order_id: str) -> Optional[Order]:
        """
        Get order details.

        Args:
            order_id: Order identifier

        Returns:
            Order object or None if not found
        """
        return self.orders.get(order_id)

    def _simulate_fill_price(self, order: Order) -> float:
        """
        Simulate a fill price for paper trading.

        Args:
            order: Order object

        Returns:
            Simulated fill price
        """
        # Simple simulation: use limit price for LIMIT orders, or a dummy market price
        if order.order_type == OrderType.LIMIT and order.price:
            return order.price
        else:
            # Dummy market price around 1500 for simulation
            return 1500.0 + (1 if order.side == OrderSide.BUY else -1) * 5.0

    def _on_fill(self, order_id: str, fill_price: float, fill_qty: int):
        """
        Handle order fill event.

        Args:
            order_id: Filled order ID
            fill_price: Execution price
            fill_qty: Filled quantity
        """
        if order_id not in self.orders:
            logger.error(f"Fill received for unknown order {order_id}")
            return

        order = self.orders[order_id]
        order.status = OrderStatus.FILLED
        order.fill_price = fill_price

        # Calculate slippage
        expected_price = order.price if order.price else self._simulate_fill_price(order)
        order.slippage = fill_price - expected_price

        # Update positions
        symbol = order.symbol
        if symbol not in self.positions:
            self.positions[symbol] = 0

        if order.side == OrderSide.BUY:
            self.positions[symbol] += fill_qty
        elif order.side == OrderSide.SELL:
            self.positions[symbol] -= fill_qty

        logger.info(f"Order {order_id} FILLED at {fill_price}. Slippage: {order.slippage:.2f}")
