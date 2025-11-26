from __future__ import annotations

"""Base broker interface for mock/paper/live adapters.

This layer is side-effect free beyond broker API calls; it does not perform
risk checks or strategy logic.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Iterable, Optional


class OrderSide(str, Enum):
    BUY = "BUY"
    SELL = "SELL"


class OrderType(str, Enum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP = "STOP"
    STOP_LIMIT = "STOP_LIMIT"


class OrderStatus(str, Enum):
    NEW = "NEW"
    FILLED = "FILLED"
    PARTIALLY_FILLED = "PARTIALLY_FILLED"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"


@dataclass
class Order:
    id: Optional[str]
    symbol: str
    side: OrderSide
    quantity: int
    order_type: OrderType
    price: Optional[float] = None
    status: OrderStatus = OrderStatus.NEW
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    external_id: Optional[str] = None  # broker-specific ID
    avg_fill_price: Optional[float] = None
    filled_quantity: int = 0


@dataclass
class Position:
    symbol: str
    quantity: int
    avg_price: float
    realized_pnl: float = 0.0
    unrealized_pnl: float = 0.0


@dataclass
class Balance:
    available: float
    equity: float
    currency: str = "INR"


class BaseBroker(ABC):
    """Interface for execution adapters."""

    @abstractmethod
    def place_order(self, order: Order) -> Order:
        """Submit an order; may fill immediately for mock/paper."""

    @abstractmethod
    def cancel_order(self, order_id: str) -> bool:
        """Cancel an open order."""

    @abstractmethod
    def get_order_status(self, order_id: str) -> Optional[Order]:
        """Fetch latest status for an order."""

    @abstractmethod
    def list_positions(self) -> Iterable[Position]:
        """Return current open positions."""

    @abstractmethod
    def get_balance(self) -> Balance:
        """Return account balance/equity snapshot."""

