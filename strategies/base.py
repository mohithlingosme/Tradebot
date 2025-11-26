from __future__ import annotations

"""Canonical strategy interface shared across trading flows."""

from typing import Literal, Protocol

from common.market_data import Candle

Signal = Literal["BUY", "SELL", "NONE"]


class Strategy(Protocol):
    """Minimal interface for streaming-candle strategies."""

    def update(self, candle: Candle) -> None:
        """Consume a new candle and update internal indicators."""

    def signal(self) -> Signal:
        """Return the latest actionable trading signal."""

