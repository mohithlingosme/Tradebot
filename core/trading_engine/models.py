"""
Shared data models for the Phase 4 trading engine.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class SignalAction(Enum):
    BUY = "buy"
    SELL = "sell"
    FLAT = "flat"  # close/flatten existing exposure


class OrderSide(Enum):
    BUY = "buy"
    SELL = "sell"


class OrderType(Enum):
    MARKET = "market"
    LIMIT = "limit"


class OrderStatus(Enum):
    PENDING = "pending"
    FILLED = "filled"
    PARTIALLY_FILLED = "partially_filled"
    REJECTED = "rejected"


class RiskDecisionType(Enum):
    ALLOW = "allow"
    REJECT = "reject"
    MODIFY = "modify"


class CircuitBreakerState(Enum):
    ARMED = "armed"
    TRIGGERED = "triggered"
    RESET = "reset"


@dataclass
class Bar:
    """OHLCV bar."""

    symbol: str
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float = 0.0


@dataclass
class Tick:
    """Tick-level quote or trade."""

    symbol: str
    timestamp: datetime
    price: float
    size: float = 0.0


@dataclass
class Signal:
    """Strategy output signal."""

    symbol: str
    action: SignalAction
    size: Optional[float] = None  # None means delegate to position sizing
    confidence: float = 0.0
    timestamp: datetime = field(default_factory=_utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class OrderRequest:
    """Order request flowing through the engine."""

    symbol: str
    side: OrderSide
    quantity: float
    order_type: OrderType = OrderType.MARKET
    limit_price: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    trailing_stop: Optional[float] = None
    strategy_name: Optional[str] = None
    created_at: datetime = field(default_factory=_utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class OrderFill:
    """Result of order simulation/execution."""

    order: OrderRequest
    filled_quantity: float
    fill_price: float
    status: OrderStatus
    pnl: float = 0.0
    timestamp: datetime = field(default_factory=_utcnow)
    reason: Optional[str] = None


@dataclass
class PortfolioPosition:
    """Single-symbol position with MTM tracking."""

    symbol: str
    quantity: float = 0.0
    average_price: float = 0.0
    last_price: float = 0.0
    realized_pnl: float = 0.0
    unrealized_pnl: float = 0.0
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    trailing_stop: Optional[float] = None
    peak_price: Optional[float] = None
    entry_time: Optional[datetime] = None

    def market_value(self) -> float:
        return self.quantity * self.last_price

    def update_price(self, price: float) -> None:
        self.last_price = price
        self.unrealized_pnl = (self.last_price - self.average_price) * self.quantity
        if self.peak_price is None or price > self.peak_price:
            self.peak_price = price


@dataclass
class PortfolioState:
    """Aggregated portfolio snapshot."""

    cash: float
    positions: Dict[str, PortfolioPosition] = field(default_factory=dict)
    realized_pnl: float = 0.0
    daily_start_equity: Optional[float] = None
    last_timestamp: Optional[datetime] = None

    @property
    def equity(self) -> float:
        return self.cash + sum(pos.market_value() for pos in self.positions.values())

    @property
    def exposure(self) -> float:
        return sum(abs(pos.market_value()) for pos in self.positions.values())

    @property
    def unrealized_pnl(self) -> float:
        return sum(pos.unrealized_pnl for pos in self.positions.values())

    @property
    def daily_pnl(self) -> float:
        start = self.daily_start_equity if self.daily_start_equity is not None else self.equity
        return self.equity - start


@dataclass
class RiskDecision:
    """Risk manager decision for an order."""

    decision: RiskDecisionType
    order: Optional[OrderRequest]
    reason: Optional[str] = None
