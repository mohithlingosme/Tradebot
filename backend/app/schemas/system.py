"""Schemas for system-level responses."""

from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class DependencyHealth(BaseModel):
    name: str
    healthy: bool
    last_checked: datetime
    message: Optional[str] = None


class StatusResponse(BaseModel):
    app_version: str = Field(..., example="1.1.0")
    uptime_seconds: float = Field(..., example=12345.5)
    environment: str = Field(..., example="development")
    dependencies_ok: Dict[str, bool] = Field(
        ..., example={"database": True, "market_data": True}
    )
    dependency_details: List[DependencyHealth] = Field(default_factory=list)


class LogEntry(BaseModel):
    timestamp: datetime
    level: str
    message: str
    source: str


class LogsResponse(BaseModel):
    entries: List[LogEntry]
    total: int


class MetricsResponse(BaseModel):
    active_strategies: int
    open_positions: int
    today_trades_count: int
    pnl_today: float
    request_per_second: float
