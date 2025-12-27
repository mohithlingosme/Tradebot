from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import List

from pydantic import BaseModel, Field, model_validator


class LoginRequest(BaseModel):
    email: str | None = Field(default=None, description="Primary login identifier (email).")
    username: str | None = Field(
        default=None,
        description="Legacy alias for email (UI historically labeled this as username).",
    )
    password: str

    @model_validator(mode="after")
    def _ensure_identifier(cls, values: "LoginRequest") -> "LoginRequest":
        if not (values.email or values.username):
            raise ValueError("Either email or username must be provided.")
        return values

    def identifier(self) -> str:
        """Return the normalized login identifier (email-compatible)."""
        value = self.email or self.username or ""
        return value.strip()


class RegimeHistoryPoint(BaseModel):
    timestamp: datetime
    label: str
    probability: float
    volatility: float


class RegimeResponse(BaseModel):
    symbol: str
    current_regime: str
    probability: float
    realized_volatility: float
    atr: float
    window: int
    updated_at: datetime
    history: List[RegimeHistoryPoint]


class OrderBookLevel(BaseModel):
    price: float
    size: float


class OrderBookHistoryPoint(BaseModel):
    timestamp: datetime
    imbalance: float
    state: str


class OrderBookAnalyticsResponse(BaseModel):
    symbol: str
    timestamp: datetime
    imbalance: float
    state: str
    spread: float
    buy_pressure: float
    sell_pressure: float
    best_bid: float | None
    best_ask: float | None
    bids: List[OrderBookLevel]
    asks: List[OrderBookLevel]
    history: List[OrderBookHistoryPoint]


class PnLResponse(BaseModel):
    total_pnl: float
    day_pnl: float
    unrealized_pnl: float
    realized_pnl: float


class OrderSnapshot(BaseModel):
    id: int
    symbol: str
    side: str
    quantity: float
    price: float
    order_type: str
    status: str
    timestamp: datetime


class TradeSnapshot(BaseModel):
    id: int
    symbol: str
    side: str
    quantity: float
    price: float
    status: str
    timestamp: datetime


class PlaceOrderRequest(BaseModel):
    symbol: str
    side: str  # 'buy' or 'sell'
    qty: int
    price: float | None = None  # None for market order


class CancelOrderRequest(BaseModel):
    order_id: int


class ModifyOrderRequest(BaseModel):
    order_id: int
    qty: int | None = None
    price: float | None = None


class OrderResponse(BaseModel):
    id: str
    symbol: str
    side: str
    qty: int
    price: float | None
    status: str
    created_at: datetime
    filled_at: datetime | None


class LogEntry(BaseModel):
    timestamp: datetime
    level: str
    message: str
    source: str


class UserCreate(BaseModel):
    email: str
    password: str
    username: Optional[str] = None


class UserUpdate(BaseModel):
    username: Optional[str] = None
    is_active: Optional[bool] = None


class PasswordChange(BaseModel):
    current_password: str
    new_password: str
