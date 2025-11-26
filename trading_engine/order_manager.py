"""
Order Manager Module

Responsibilities:
- Receive trading signals from strategies
- Create and manage orders (market, limit, stop)
- Handle order lifecycle (submit, modify, cancel)

Interfaces:
- create_order(signal, symbol, quantity, order_type)
- submit_order(order)
- cancel_order(order_id)
- get_order_status(order_id)
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime
from enum import Enum

from execution.base_broker import BaseBroker, Order as BrokerOrder, OrderSide, OrderStatus, OrderType

logger = logging.getLogger(__name__)

class Order:
    """
    Represents a trading order.
    """

    def __init__(self, order_id: str, symbol: str, side: OrderSide, quantity: int,
                 order_type: OrderType, price: Optional[float] = None,
                 stop_price: Optional[float] = None):
        """
        Initialize order.

        Args:
            order_id: Unique order identifier
            symbol: Trading symbol
            side: Buy or sell
            quantity: Order quantity
            order_type: Type of order
            price: Limit price (for limit orders)
            stop_price: Stop price (for stop orders)
        """
        self.order_id = order_id
        self.symbol = symbol
        self.side = side
        self.quantity = quantity
        self.order_type = order_type
        self.price = price
        self.stop_price = stop_price
        self.status = OrderStatus.NEW
        self.timestamp = datetime.now()
        self.filled_quantity = 0
        self.average_price = 0.0

    def to_dict(self) -> Dict:
        """Convert order to dictionary representation."""
        return {
            'order_id': self.order_id,
            'symbol': self.symbol,
            'side': self.side.value,
            'quantity': self.quantity,
            'order_type': self.order_type.value,
            'price': self.price,
            'stop_price': self.stop_price,
            'status': self.status.value,
            'timestamp': self.timestamp.isoformat(),
            'filled_quantity': self.filled_quantity,
            'average_price': self.average_price
        }

class OrderManager:
    """
    Manages the creation, submission, and tracking of trading orders.
    """

    def __init__(self, broker_interface):
        """
        Initialize order manager.

        Args:
            broker_interface: Interface to broker for order execution
        """
        self.broker = broker_interface
        self.orders = {}  # order_id -> Order
        self.logger = logging.getLogger(f"{__name__}.OrderManager")

    def create_order(self, signal: Dict, symbol: str, quantity: int,
                    order_type: OrderType = OrderType.MARKET,
                    price: Optional[float] = None,
                    stop_price: Optional[float] = None) -> Order:
        """
        Create a new order from trading signal.

        Args:
            signal: Trading signal dictionary
            symbol: Trading symbol
            quantity: Order quantity
            order_type: Type of order
            price: Limit price
            stop_price: Stop price

        Returns:
            Created Order object
        """
        order_id = f"order_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{symbol}"
        side = OrderSide.BUY if str(signal.get('action')).lower() == 'buy' else OrderSide.SELL

        order = Order(order_id, symbol, side, quantity, order_type, price, stop_price)
        self.orders[order_id] = order

        self.logger.info(f"Created order: {order_id} for {symbol} {side.value} {quantity}")
        return order

    def submit_order(self, order: Order) -> bool:
        """
        Submit order to broker for execution.

        Args:
            order: Order to submit

        Returns:
            True if submitted successfully, False otherwise
        """
        try:
            broker_order = BrokerOrder(
                id=order.order_id,
                symbol=order.symbol,
                side=order.side,
                quantity=order.quantity,
                order_type=order.order_type,
                price=order.price,
            )
            broker_response = self.broker.place_order(broker_order) if isinstance(self.broker, BaseBroker) else None
            if broker_response:
                order.status = broker_response.status
                order.filled_quantity = broker_response.filled_quantity
                order.average_price = broker_response.avg_fill_price or order.price or 0.0
            else:
                order.status = OrderStatus.FILLED
                order.filled_quantity = order.quantity
                order.average_price = order.price or 0.0
            self.logger.info(f"Submitted order: {order.order_id} with status {order.status.value}")
            return order.status not in {OrderStatus.REJECTED, OrderStatus.CANCELLED}
        except Exception as e:
            self.logger.error(f"Failed to submit order {order.order_id}: {e}")
            order.status = OrderStatus.REJECTED
            return False

    def cancel_order(self, order_id: str) -> bool:
        """
        Cancel a pending order.

        Args:
            order_id: ID of order to cancel

        Returns:
            True if cancelled successfully, False otherwise
        """
        if order_id not in self.orders:
            self.logger.error(f"Order not found: {order_id}")
            return False

        order = self.orders[order_id]
        if order.status in [OrderStatus.FILLED, OrderStatus.CANCELLED, OrderStatus.REJECTED]:
            self.logger.error(f"Cannot cancel order {order_id} with status {order.status.value}")
            return False

        try:
            if isinstance(self.broker, BaseBroker):
                if not self.broker.cancel_order(order_id):
                    self.logger.error(f"Broker failed to cancel order {order_id}")
                    return False
            order.status = OrderStatus.CANCELLED
            self.logger.info(f"Cancelled order: {order_id}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to cancel order {order_id}: {e}")
            return False

    def get_order_status(self, order_id: str) -> Optional[Dict]:
        """
        Get current status of an order.

        Args:
            order_id: Order ID

        Returns:
            Order status dictionary or None if not found
        """
        if order_id not in self.orders:
            return None

        order = self.orders[order_id]
        # TODO: Query broker for latest status if needed
        return order.to_dict()

    def get_all_orders(self, status_filter: Optional[OrderStatus] = None) -> List[Dict]:
        """
        Get all orders, optionally filtered by status.

        Args:
            status_filter: Optional status to filter by

        Returns:
            List of order dictionaries
        """
        orders = self.orders.values()
        if status_filter:
            orders = [o for o in orders if o.status == status_filter]

        return [order.to_dict() for order in orders]

    def update_order_status(self, order_id: str, status: OrderStatus,
                          filled_quantity: int = 0, average_price: float = 0.0) -> bool:
        """
        Update order status (typically called by broker interface).

        Args:
            order_id: Order ID
            status: New status
            filled_quantity: Quantity filled
            average_price: Average fill price

        Returns:
            True if updated successfully
        """
        if order_id not in self.orders:
            self.logger.error(f"Order not found for update: {order_id}")
            return False

        order = self.orders[order_id]
        order.status = status
        order.filled_quantity = filled_quantity
        order.average_price = average_price

        self.logger.info(f"Updated order {order_id}: status={status.value}, "
                        f"filled={filled_quantity}, avg_price={average_price}")
        return True
