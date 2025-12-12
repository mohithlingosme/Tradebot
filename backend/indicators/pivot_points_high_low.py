"""
Pivot highs/lows detector.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Sequence


@dataclass
class PivotPointsHighLow:
    """Identify local extrema based on lookback/lookforward windows."""

    left: int = 3
    right: int = 3

    def calculate(self, high: Sequence[float], low: Sequence[float]) -> Optional[str]:
        series = self.calculate_series(high, low)
        return series[-1] if series else None

    def calculate_series(self, high: Sequence[float], low: Sequence[float]) -> List[Optional[str]]:
        if len(high) != len(low):
            return []
        output: List[Optional[str]] = [None] * len(high)
        for i in range(self.left, len(high) - self.right):
            window_high = high[i - self.left : i + self.right + 1]
            window_low = low[i - self.left : i + self.right + 1]
            if high[i] == max(window_high):
                output[i] = "pivot_high"
            elif low[i] == min(window_low):
                output[i] = "pivot_low"
        return output
