from __future__ import annotations

from datetime import datetime
from typing import List

from pydantic import BaseModel


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
