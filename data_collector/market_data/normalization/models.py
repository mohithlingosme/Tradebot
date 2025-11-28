"""
Canonical Pydantic models for market data.
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional, Annotated
from pydantic import BaseModel, Field
from pydantic.functional_validators import field_validator
from uuid import UUID

# Type aliases for common decimal constraints
PositiveDecimal = Annotated[Decimal, Field(ge=0)]


class Trade(BaseModel):
    """Canonical trade model."""
    provider_id: int
    instrument_id: int
    trade_id: Optional[str] = None
    price: PositiveDecimal
    size: PositiveDecimal
    side: str = Field(..., pattern=r'^(buy|sell|unknown)$')
    event_time: datetime
    received_at: datetime
    ingest_id: UUID


class Quote(BaseModel):
    """Canonical quote model."""
    provider_id: int
    instrument_id: int
    bid_price: Optional[PositiveDecimal] = None
    bid_size: Optional[PositiveDecimal] = None
    ask_price: Optional[PositiveDecimal] = None
    ask_size: Optional[PositiveDecimal] = None
    last_price: Optional[PositiveDecimal] = None
    last_size: Optional[PositiveDecimal] = None
    event_time: datetime
    received_at: datetime
    ingest_id: UUID


class Candle(BaseModel):
    """Canonical candle model."""
    provider_id: int
    instrument_id: int
    granularity: str = Field(..., pattern=r'^\d+[mhd]$')  # e.g., '1m', '5m', '1h', '1d'
    bucket_start: datetime
    open_price: PositiveDecimal
    high_price: PositiveDecimal
    low_price: PositiveDecimal
    close_price: PositiveDecimal
    volume: PositiveDecimal
    event_time: datetime
    received_at: datetime
    ingest_id: UUID
