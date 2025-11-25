"""Schemas for position data."""

from datetime import datetime
from typing import List

from pydantic import BaseModel

from .common import PaginatedResponse


class Position(BaseModel):
    symbol: str
    side: str
    quantity: float
    avg_price: float
    current_price: float
    realized_pnl: float
    unrealized_pnl: float
    last_update: datetime


class PositionsResponse(PaginatedResponse):
    items: List[Position]
