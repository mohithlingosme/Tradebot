"""
RSI divergence helper.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional, Sequence

from .rsi import RSI


@dataclass
class RSIDivergenceIndicator:
    """Compare recent highs/lows in price vs RSI to flag simple divergences."""

    period: int = 14

    def calculate(self, close: Sequence[float]) -> Optional[Dict[str, bool]]:
        if len(close) < self.period * 2:
            return None
        midpoint = len(close) - self.period
        first_prices = close[midpoint - self.period : midpoint]
        recent_prices = close[midpoint:]

        rsi_indicator = RSI(period=self.period)
        rsi_series = rsi_indicator.calculate_series(list(close))
        first_rsi = [val for val in rsi_series[midpoint - self.period : midpoint] if val is not None]
        recent_rsi = [val for val in rsi_series[midpoint:] if val is not None]
        if not first_rsi or not recent_rsi:
            return None
        bearish = max(recent_prices) > max(first_prices) and max(recent_rsi) < max(first_rsi)
        bullish = min(recent_prices) < min(first_prices) and min(recent_rsi) > min(first_rsi)
        return {"bullish": bullish, "bearish": bearish}
