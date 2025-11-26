from __future__ import annotations

"""
Pydantic models for Phase 3 ingestion artifacts.
"""

from datetime import date, datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class PriceBar(BaseModel):
    """Daily OHLCV bar."""

    symbol: str
    trade_date: date
    open: float
    high: float
    low: float
    close: float
    volume: float
    provider: str = Field(default="yfinance")
    is_index: bool = Field(default=False)


class AnomalyType(str, Enum):
    VOLUME_SPIKE = "volume_spike"
    PRICE_GAP = "price_gap"
    PRICE_MOVE = "price_move"


class Anomaly(BaseModel):
    """Represents an anomaly detected on a given trading day."""

    symbol: str
    trade_date: date
    anomaly_type: AnomalyType
    metric_value: Optional[float] = None
    reference_value: Optional[float] = None
    magnitude: Optional[float] = None
    details: Dict[str, Any] = Field(default_factory=dict)
    provider: str = Field(default="yfinance")


class NewsArticle(BaseModel):
    """Normalized article with optional symbol mapping."""

    article_id: str
    symbol: str
    company_name: Optional[str] = None
    headline: str
    summary: Optional[str] = None
    source: Optional[str] = None
    url: str
    published_at: datetime
    sentiment_score: Optional[float] = None
    sentiment_label: Optional[str] = None
    raw: Dict[str, Any] = Field(default_factory=dict)


class DailySentiment(BaseModel):
    """Aggregated sentiment per symbol per market date."""

    symbol: str
    market_date: date
    mean_sentiment: Optional[float] = None
    max_sentiment: Optional[float] = None
    article_count: int = 0
    source: str = "newsapi"


class MacroIndicator(BaseModel):
    """Macro-economic or market-wide indicator."""

    metric_name: str
    as_of_date: date
    value: float
    source: str


class FundamentalRecord(BaseModel):
    """Fundamental metrics per symbol per period."""

    symbol: str
    period_start: date
    period_end: date
    period_type: str = Field(default="quarterly")
    pe: Optional[float] = None
    eps: Optional[float] = None
    roe: Optional[float] = None
    revenue: Optional[float] = None
    profit: Optional[float] = None
    market_cap: Optional[float] = None
    source: str = "yfinance"
    currency: str = "INR"


class FeatureRow(BaseModel):
    """ML-ready feature vector stored as JSON."""

    symbol: str
    as_of_date: date
    version: str = "v1"
    feature_vector: Dict[str, float]
    label: Optional[float] = None

