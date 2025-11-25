"""Portfolio-related response models."""

from pydantic import BaseModel, Field
from typing import List, Optional


class PositionSummary(BaseModel):
    symbol: str
    quantity: float
    avg_price: float
    market_price: float
    unrealized_pnl: float


class PortfolioSummary(BaseModel):
    equity: float
    cash: float
    total_value: float
    pnl_day: float
    pnl_total: float
    leverage: Optional[float] = None


class PortfolioResponse(BaseModel):
    summary: PortfolioSummary
    positions: List[PositionSummary]
    timestamp: str = Field(..., example="2024-01-01T00:00:00Z")
