"""
Event schemas for realtime updates.

All events follow a standard envelope format for consistency and versioning.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional, Union
from uuid import uuid4

from pydantic import BaseModel, Field


class EventType(str, Enum):
    """Supported event types for realtime updates."""
    ORDER_CREATED = "order.created"
    ORDER_UPDATED = "order.updated"
    ORDER_FILLED = "order.filled"
    ORDER_REJECTED = "order.rejected"
    POSITION_UPDATED = "position.updated"
    PNL_UPDATED = "pnl.updated"
    RISK_LIMIT_HIT = "risk.limit_hit"
    MARGIN_ALERT = "margin.alert"
    NOTIFICATION_CREATED = "notification.created"


class EventEnvelope(BaseModel):
    """Standard envelope for all realtime events."""
    event_id: str = Field(default_factory=lambda: str(uuid4()), description="Unique event identifier")
    type: EventType = Field(..., description="Event type")
    ts: datetime = Field(default_factory=datetime.utcnow, description="Event timestamp (UTC)")
    entity_id: str = Field(..., description="ID of the entity this event relates to")
    user_id: str = Field(..., description="User ID this event is for")
    payload: Dict[str, Any] = Field(..., description="Event-specific data")
    version: str = Field(default="1.0", description="Event schema version")

    class Config:
        use_enum_values = True


# Order Events
class OrderCreatedEvent(BaseModel):
    """Event fired when a new order is created."""
    order_id: str
    symbol: str
    side: str  # buy/sell
    quantity: float
    price: Optional[float]
    order_type: str
    status: str = "pending"


class OrderUpdatedEvent(BaseModel):
    """Event fired when an order is updated."""
    order_id: str
    status: str
    filled_quantity: Optional[float] = None
    average_price: Optional[float] = None


class OrderFilledEvent(BaseModel):
    """Event fired when an order is completely filled."""
    order_id: str
    filled_quantity: float
    average_price: float
    total_value: float


class OrderRejectedEvent(BaseModel):
    """Event fired when an order is rejected."""
    order_id: str
    reason: str


# Position Events
class PositionUpdatedEvent(BaseModel):
    """Event fired when a position changes."""
    symbol: str
    quantity: float
    average_price: float
    current_price: float
    unrealized_pnl: float
    realized_pnl: float


# P&L Events
class PnlUpdatedEvent(BaseModel):
    """Event fired when P&L changes."""
    account_id: str
    total_pnl: float
    daily_pnl: float
    unrealized_pnl: float
    realized_pnl: float


# Risk Events
class RiskLimitHitEvent(BaseModel):
    """Event fired when a risk limit is hit."""
    limit_type: str  # e.g., "max_loss", "max_drawdown"
    current_value: float
    threshold: float
    severity: str = "warning"  # warning/critical


class MarginAlertEvent(BaseModel):
    """Event fired for margin-related alerts."""
    account_id: str
    margin_used: float
    margin_available: float
    margin_level: float
    alert_type: str  # "low_margin", "margin_call"


# Notification Events
class NotificationCreatedEvent(BaseModel):
    """Event fired when a new notification is created."""
    notification_id: str
    title: str
    message: str
    type: str  # info/warning/error/success
    priority: str = "normal"  # low/normal/high


def create_event_envelope(
    event_type: EventType,
    entity_id: str,
    user_id: str,
    payload: Union[BaseModel, Dict[str, Any]],
    version: str = "1.0"
) -> EventEnvelope:
    """Helper function to create a standardized event envelope."""
    if isinstance(payload, BaseModel):
        payload_dict = payload.dict()
    else:
        payload_dict = payload

    return EventEnvelope(
        type=event_type,
        entity_id=entity_id,
        user_id=user_id,
        payload=payload_dict,
        version=version
    )
