"""
Paper Trading Engine

Simulates trading with virtual money for practice and strategy testing.
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime
from decimal import Decimal
from enum import Enum

logger = logging.getLogger(__name__)


class OrderType(Enum):
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"


class OrderSide(Enum):
    BUY = "buy"
    SELL = "sell"


class OrderStatus(Enum):
    PENDING = "pending"
    FILLED = "filled"
    PARTIALLY_FILLED = "partially_filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"


class PaperOrder:
    """Represents a paper trading order."""

    def __init__(
        self,
        order_id: str,
        symbol: str,
        side: str,
        quantity: float,
        order_type: str = "market",
        price: Optional[float] = None,
        stop_price: Optional[float] = None,
    ):
        self.order_id = order_id
        self.symbol = symbol
        self.side = OrderSide(side.lower())
        self.quantity = Decimal(str(quantity))
        self.order_type = OrderType(order_type.lower())
        self.price = Decimal(str(price)) if price else None
        self.stop_price = Decimal(str(stop_price)) if stop_price else None
        self.status = OrderStatus.PENDING
        self.filled_quantity = Decimal('0')
        self.avg_fill_price = Decimal('0')
        self.created_at = datetime.now()
        self.filled_at: Optional[datetime] = None

    def fill(self, fill_price: float, fill_quantity: Optional[float] = None):
        """Fill the order at given price."""
        fill_qty = Decimal(str(fill_quantity)) if fill_quantity else self.quantity
        fill_price_decimal = Decimal(str(fill_price))
        
        total_cost = (self.avg_fill_price * self.filled_quantity) + (fill_price_decimal * fill_qty)
        self.filled_quantity += fill_qty
        self.avg_fill_price = total_cost / self.filled_quantity if self.filled_quantity > 0 else Decimal('0')
        
        if self.filled_quantity >= self.quantity:
            self.status = OrderStatus.FILLED
            self.filled_at = datetime.now()
        elif self.filled_quantity > 0:
            self.status = OrderStatus.PARTIALLY_FILLED

    def cancel(self):
        """Cancel the order."""
        self.status = OrderStatus.CANCELLED

    def to_dict(self) -> Dict:
        """Convert order to dictionary."""
        return {
            "order_id": self.order_id,
            "symbol": self.symbol,
            "side": self.side.value,
            "quantity": float(self.quantity),
            "order_type": self.order_type.value,
            "price": float(self.price) if self.price else None,
            "stop_price": float(self.stop_price) if self.stop_price else None,
            "status": self.status.value,
            "filled_quantity": float(self.filled_quantity),
            "avg_fill_price": float(self.avg_fill_price),
            "created_at": self.created_at.isoformat(),
            "filled_at": self.filled_at.isoformat() if self.filled_at else None,
        }


class PaperPosition:
    """Represents a paper trading position."""

    def __init__(self, symbol: str):
        self.symbol = symbol
        self.quantity = Decimal('0')
        self.average_entry_price = Decimal('0')
        self.current_price = Decimal('0')
        self.unrealized_pnl = Decimal('0')
        self.realized_pnl = Decimal('0')
        self.total_cost = Decimal('0')
        self.last_update = datetime.now()

    def add_quantity(self, quantity: float, price: float):
        """Add to position."""
        qty = Decimal(str(quantity))
        prc = Decimal(str(price))
        
        total_cost = self.total_cost + (qty * prc)
        self.quantity += qty
        self.average_entry_price = total_cost / self.quantity if self.quantity > 0 else Decimal('0')
        self.total_cost = total_cost
        self.last_update = datetime.now()
        self._update_unrealized_pnl()

    def reduce_quantity(self, quantity: float, price: float):
        """Reduce position."""
        qty = Decimal(str(quantity))
        prc = Decimal(str(price))
        
        if self.quantity >= qty:
            # Calculate realized P&L
            realized = (prc - self.average_entry_price) * qty
            self.realized_pnl += realized
            
            # Update cost basis
            cost_to_remove = self.average_entry_price * qty
            self.total_cost -= cost_to_remove
            self.quantity -= qty
            
            if self.quantity == 0:
                self.average_entry_price = Decimal('0')
            
            self.last_update = datetime.now()
            self._update_unrealized_pnl()
            return float(realized)
        return 0.0

    def update_price(self, current_price: float):
        """Update current market price."""
        self.current_price = Decimal(str(current_price))
        self._update_unrealized_pnl()
        self.last_update = datetime.now()

    def _update_unrealized_pnl(self):
        """Calculate unrealized P&L."""
        if self.quantity > 0 and self.average_entry_price > 0:
            self.unrealized_pnl = (self.current_price - self.average_entry_price) * self.quantity
        else:
            self.unrealized_pnl = Decimal('0')

    def to_dict(self) -> Dict:
        """Convert position to dictionary."""
        return {
            "symbol": self.symbol,
            "quantity": float(self.quantity),
            "average_entry_price": float(self.average_entry_price),
            "current_price": float(self.current_price),
            "unrealized_pnl": float(self.unrealized_pnl),
            "realized_pnl": float(self.realized_pnl),
            "total_pnl": float(self.unrealized_pnl + self.realized_pnl),
            "market_value": float(self.current_price * self.quantity),
            "last_update": self.last_update.isoformat(),
        }


class PaperTradingEngine:
    """Paper trading engine for simulated trading."""

    def __init__(self, initial_cash: float = 100000.0):
        """
        Initialize paper trading engine.

        Args:
            initial_cash: Starting cash amount (default: $100,000)
        """
        self.initial_cash = Decimal(str(initial_cash))
        self.cash = Decimal(str(initial_cash))
        self.positions: Dict[str, PaperPosition] = {}
        self.orders: Dict[str, PaperOrder] = {}
        self.order_history: List[Dict] = []
        self.trade_history: List[Dict] = []
        self.order_counter = 0
        logger.info(f"Paper trading engine initialized with ${initial_cash:,.2f}")

    def place_order(
        self,
        symbol: str,
        side: str,
        quantity: float,
        order_type: str = "market",
        price: Optional[float] = None,
        stop_price: Optional[float] = None,
        current_market_price: Optional[float] = None,
    ) -> Dict:
        """
        Place a paper trading order.

        Args:
            symbol: Trading symbol
            side: 'buy' or 'sell'
            quantity: Order quantity
            order_type: 'market', 'limit', or 'stop'
            price: Limit/stop price
            current_market_price: Current market price (for market orders)

        Returns:
            Order result dictionary
        """
        self.order_counter += 1
        order_id = f"PAPER_{self.order_counter:06d}"
        
        order = PaperOrder(
            order_id=order_id,
            symbol=symbol,
            side=side,
            quantity=quantity,
            order_type=order_type,
            price=price,
            stop_price=stop_price,
        )

        # Determine fill price
        fill_price = None
        if order_type == "market":
            fill_price = current_market_price or price or self._get_current_price(symbol)
        elif order_type == "limit" and price:
            # For limit orders, check if price is favorable
            current_price = current_market_price or self._get_current_price(symbol)
            if side.lower() == "buy" and current_price <= price:
                fill_price = price
            elif side.lower() == "sell" and current_price >= price:
                fill_price = price
        elif order_type == "stop" and stop_price:
            current_price = current_market_price or self._get_current_price(symbol)
            if side.lower() == "buy" and current_price >= stop_price:
                fill_price = stop_price
            elif side.lower() == "sell" and current_price <= stop_price:
                fill_price = stop_price

        # Check if order can be executed
        if fill_price:
            # Validate order
            if side.lower() == "buy":
                cost = Decimal(str(quantity)) * Decimal(str(fill_price))
                if cost > self.cash:
                    order.status = OrderStatus.REJECTED
                    return {
                        "order_id": order_id,
                        "status": "rejected",
                        "message": "Insufficient cash"
                    }
            elif side.lower() == "sell":
                if symbol not in self.positions or self.positions[symbol].quantity < quantity:
                    order.status = OrderStatus.REJECTED
                    return {
                        "order_id": order_id,
                        "status": "rejected",
                        "message": "Insufficient position"
                    }

            # Execute order
            order.fill(fill_price)
            self._execute_order(order, fill_price)
        
        self.orders[order_id] = order
        
        result = order.to_dict()
        result["fill_price"] = float(fill_price) if fill_price else None
        return result

    def _execute_order(self, order: PaperOrder, fill_price: float):
        """Execute an order and update positions."""
        fill_price_decimal = Decimal(str(fill_price))
        qty = order.filled_quantity
        
        if order.side == OrderSide.BUY:
            # Update cash
            cost = qty * fill_price_decimal
            self.cash -= cost
            
            # Update position
            if order.symbol not in self.positions:
                self.positions[order.symbol] = PaperPosition(order.symbol)
            self.positions[order.symbol].add_quantity(float(qty), fill_price)
            
        else:  # SELL
            # Update cash
            proceeds = qty * fill_price_decimal
            self.cash += proceeds
            
            # Update position
            if order.symbol in self.positions:
                realized_pnl = self.positions[order.symbol].reduce_quantity(float(qty), fill_price)
            
        # Record trade
        self.trade_history.append({
            "order_id": order.order_id,
            "symbol": order.symbol,
            "side": order.side.value,
            "quantity": float(qty),
            "price": fill_price,
            "timestamp": order.filled_at.isoformat() if order.filled_at else datetime.now().isoformat(),
        })
        
        logger.info(f"Paper trade executed: {order.symbol} {order.side.value} {qty} @ {fill_price}")

    def _get_current_price(self, symbol: str) -> float:
        """Get current market price (mock implementation)."""
        # In production, fetch from market data
        # For now, return a default price
        return 100.0

    def update_prices(self, price_updates: Dict[str, float]):
        """Update current prices for all positions."""
        for symbol, price in price_updates.items():
            if symbol in self.positions:
                self.positions[symbol].update_price(price)

    def get_portfolio_summary(self) -> Dict:
        """Get portfolio summary."""
        positions_value = sum(
            float(pos.current_price * pos.quantity)
            for pos in self.positions.values()
        )
        
        total_unrealized_pnl = sum(float(pos.unrealized_pnl) for pos in self.positions.values())
        total_realized_pnl = sum(float(pos.realized_pnl) for pos in self.positions.values())
        total_pnl = total_unrealized_pnl + total_realized_pnl
        
        total_value = float(self.cash) + positions_value
        
        return {
            "cash": float(self.cash),
            "positions_value": positions_value,
            "total_value": total_value,
            "unrealized_pnl": total_unrealized_pnl,
            "realized_pnl": total_realized_pnl,
            "total_pnl": total_pnl,
            "initial_cash": float(self.initial_cash),
            "return_percent": (total_pnl / float(self.initial_cash)) * 100 if self.initial_cash > 0 else 0,
        }

    def get_positions(self) -> List[Dict]:
        """Get all positions."""
        return [pos.to_dict() for pos in self.positions.values() if pos.quantity > 0]

    def get_orders(self, limit: int = 50) -> List[Dict]:
        """Get recent orders."""
        return [order.to_dict() for order in list(self.orders.values())[-limit:]]

    def get_trade_history(self, limit: int = 50) -> List[Dict]:
        """Get trade history."""
        return self.trade_history[-limit:]

    def reset_portfolio(self, initial_cash: Optional[float] = None):
        """Reset paper trading portfolio."""
        self.initial_cash = Decimal(str(initial_cash)) if initial_cash else self.initial_cash
        self.cash = self.initial_cash
        self.positions.clear()
        self.orders.clear()
        self.order_history.clear()
        self.trade_history.clear()
        self.order_counter = 0
        logger.info(f"Paper trading portfolio reset with ${float(self.initial_cash):,.2f}")


# Global paper trading engine instance (per user in production)
_paper_trading_engines: Dict[str, PaperTradingEngine] = {}


def get_paper_trading_engine(username: str) -> PaperTradingEngine:
    """Get or create paper trading engine for user."""
    if username not in _paper_trading_engines:
        _paper_trading_engines[username] = PaperTradingEngine()
    return _paper_trading_engines[username]

