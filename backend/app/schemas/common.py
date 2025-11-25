"""Reusable schema primitives."""

from datetime import datetime
from pydantic import BaseModel, Field


class TimestampedModel(BaseModel):
    """Base model that carries a timestamp."""

    timestamp: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        orm_mode = True


class PaginatedResponse(BaseModel):
    """Generic pagination envelope."""

    total: int
    limit: int
    offset: int = Field(0, ge=0)

    class Config:
        orm_mode = True
