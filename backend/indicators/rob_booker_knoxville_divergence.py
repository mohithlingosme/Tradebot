"""
Rob Booker Knoxville Divergence detector.
"""

from __future__ import annotations

from dataclasses import dataclass
from statistics import mean
from typing import Dict, Optional, Sequence

from .rsi import RSI


@dataclass
class RobBookerKnoxvilleDivergence:
    """Identify simple bullish/bearish divergences similar to Booker's Knoxville approach."""

    lookback: int = 14

    def calculate(self, close: Sequence[float]) -> Optional[Dict[str, bool]]:
        if len(close) < self.lookback * 2:
            return None
        rsi_indicator = RSI(self.lookback)
        rsi_series = rsi_indicator.calculate_series(list(close))
        recent_prices = close[-self.lookback :]
        prev_prices = close[-2 * self.lookback : -self.lookback]
        recent_rsi = [x for x in rsi_series[-self.lookback :] if x is not None]
        prev_rsi = [x for x in rsi_series[-2 * self.lookback : -self.lookback] if x is not None]
        if not recent_rsi or not prev_rsi:
            return None
        bullish = min(recent_prices) < min(prev_prices) and mean(recent_rsi) > mean(prev_rsi)
        bearish = max(recent_prices) > max(prev_prices) and mean(recent_rsi) < mean(prev_rsi)
        return {"bullish": bullish, "bearish": bearish}
