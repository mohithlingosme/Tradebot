"""Schemas for trade history."""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class Trade(BaseModel):
    symbol: str
    side: str
    quantity: float
    price: float
    timestamp: datetime
    status: str
    strategy_id: Optional[str] = None


class TradesResponse(BaseModel):
    trades: List[Trade]
    total: int
    fetched_at: datetime
