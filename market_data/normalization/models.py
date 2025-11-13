"""
Canonical Pydantic models for market data.
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, Field
from uuid import UUID


class Trade(BaseModel):
    """Canonical trade model."""
    provider_id: int
    instrument_id: int
    trade_id: Optional[str] = None
    price: Decimal = Field(..., ge=0, max_digits=20, decimal_places=8)
    size: Decimal = Field(..., ge=0, max_digits=20, decimal_places=8)
    side: str = Field(..., pattern=r'^(buy|sell|unknown)$')
    event_time: datetime
    received_at: datetime
    ingest_id: UUID


class Quote(BaseModel):
    """Canonical quote model."""
    provider_id: int
    instrument_id: int
    bid_price: Optional[Decimal] = Field(None, ge=0, max_digits=20, decimal_places=8)
    bid_size: Optional[Decimal] = Field(None, ge=0, max_digits=20, decimal_places=8)
    ask_price: Optional[Decimal] = Field(None, ge=0, max_digits=20, decimal_places=8)
    ask_size: Optional[Decimal] = Field(None, ge=0, max_digits=20, decimal_places=8)
    last_price: Optional[Decimal] = Field(None, ge=0, max_digits=20, decimal_places=8)
    last_size: Optional[Decimal] = Field(None, ge=0, max_digits=20, decimal_places=8)
    event_time: datetime
    received_at: datetime
    ingest_id: UUID


class Candle(BaseModel):
    """Canonical candle model."""
    provider_id: int
    instrument_id: int
    granularity: str = Field(..., pattern=r'^\d+[mhd]$')  # e.g., '1m', '5m', '1h', '1d'
    bucket_start: datetime
    open_price: Decimal = Field(..., ge=0, max_digits=20, decimal_places=8)
    high_price: Decimal = Field(..., ge=0, max_digits=20, decimal_places=8)
    low_price: Decimal = Field(..., ge=0, max_digits=20, decimal_places=8)
    close_price: Decimal = Field(..., ge=0, max_digits=20, decimal_places=8)
    volume: Decimal = Field(..., ge=0, max_digits=20, decimal_places=8)
    event_time: datetime
    received_at: datetime
    ingest_id: UUID
