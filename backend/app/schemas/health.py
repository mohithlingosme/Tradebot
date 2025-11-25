"""Schemas for health endpoints."""

from datetime import datetime

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Health check payload."""

    status: str = Field(..., example="ok")
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        schema_extra = {
            "example": {"status": "ok", "timestamp": "2024-01-01T00:00:00Z"}
        }
