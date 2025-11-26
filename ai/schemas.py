"""Shared schemas for AI agent outputs."""

from typing import Literal

from pydantic import BaseModel, Field


class LLMSignal(BaseModel):
    """
    Structured, advisory-only signal from the Signal AI.

    This schema intentionally omits any order sizing or executable instructions.
    """

    view: Literal["long", "short", "neutral"] = Field(
        ...,
        description="Directional view from the AI.",
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="0-1 confidence score.",
    )
    horizon: Literal["intraday", "swing"] = Field(
        ...,
        description="Intended time horizon.",
    )
    stop_loss_hint: str = Field(
        "",
        description="Optional natural language hint for stop loss.",
    )
    target_hint: str = Field(
        "",
        description="Optional natural language hint for targets.",
    )
    reasoning: str = Field(
        "",
        description="Optional reasoning or justification string.",
    )

