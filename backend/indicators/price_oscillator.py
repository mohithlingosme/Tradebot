"""
Price Oscillator (same concept as PPO).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Sequence

from .utils import ema


@dataclass
class PriceOscillator:
    """Difference between fast and slow EMAs expressed as a percentage of the slow EMA."""

    fast_period: int = 12
    slow_period: int = 26

    def calculate(self, close: Sequence[float]) -> Optional[float]:
        if len(close) < max(self.fast_period, self.slow_period):
            return None
        fast = ema(close, self.fast_period)
        slow = ema(close, self.slow_period)
        if fast is None or slow is None or slow == 0:
            return None
        return 100.0 * (fast - slow) / slow

    def calculate_series(self, close: Sequence[float]) -> List[Optional[float]]:
        values: List[Optional[float]] = []
        for i in range(len(close)):
            values.append(self.calculate(close[: i + 1]))
        return values
