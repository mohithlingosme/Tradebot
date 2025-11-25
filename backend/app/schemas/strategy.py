"""Schemas for strategy control operations."""

from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class StrategyStartRequest(BaseModel):
    strategy_id: str = Field(..., example="alphadelta-v1")
    parameters: Dict[str, Any] = Field(default_factory=dict)


class StrategyStopRequest(BaseModel):
    strategy_id: Optional[str] = Field(None, example="alphadelta-v1")
    instance_id: Optional[str] = Field(None, example="instance-1234")


class StrategyActionResponse(BaseModel):
    status: str
    strategy_id: str
    instance_id: str
    message: Optional[str] = None
