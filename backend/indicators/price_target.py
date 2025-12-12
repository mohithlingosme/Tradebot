"""
Basic price target projection using ATR multiples.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional, Sequence

from .atr import ATR


@dataclass
class PriceTarget:
    """Project bullish/bearish targets using the latest ATR reading."""

    period: int = 14
    multiplier: float = 2.0

    def calculate(
        self,
        high: Sequence[float],
        low: Sequence[float],
        close: Sequence[float],
    ) -> Optional[Dict[str, float]]:
        atr_value = ATR(self.period).calculate(list(high), list(low), list(close))
        if atr_value is None:
            return None
        last_close = close[-1]
        move = atr_value * self.multiplier
        return {
            "bullish_target": float(last_close + move),
            "bearish_target": float(last_close - move),
            "atr": float(atr_value),
        }
