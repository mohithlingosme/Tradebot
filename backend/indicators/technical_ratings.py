"""
Composite technical rating helper.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional, Sequence

from .macd import MACD
from .moving_average import SMA
from .rsi import RSI


@dataclass
class TechnicalRatings:
    """Blend RSI, MACD, and moving-average filters into a coarse rating."""

    rsi_period: int = 14
    fast_ma: int = 20
    slow_ma: int = 50

    def calculate(self, close: Sequence[float]) -> Optional[Dict[str, float]]:
        if len(close) < max(self.slow_ma, self.rsi_period + 1, 35):
            return None
        rsi_indicator = RSI(self.rsi_period)
        rsi_value = rsi_indicator.calculate(list(close))

        macd_indicator = MACD()
        macd_value = macd_indicator.calculate(list(close))
        fast_ma_value = SMA(self.fast_ma).calculate(list(close))
        slow_ma_value = SMA(self.slow_ma).calculate(list(close))
        if rsi_value is None or fast_ma_value is None or slow_ma_value is None or macd_value is None:
            return None
        score = 0
        if fast_ma_value > slow_ma_value:
            score += 1
        else:
            score -= 1
        if rsi_value > 55:
            score += 1
        elif rsi_value < 45:
            score -= 1
        if macd_value["macd"] > macd_value["signal"]:
            score += 1
        else:
            score -= 1
        rating = max(-3, min(3, score))
        return {
            "rating": rating,
            "rsi": rsi_value,
            "macd": macd_value["macd"],
            "signal": macd_value["signal"],
            "fast_ma": fast_ma_value,
            "slow_ma": slow_ma_value,
        }
