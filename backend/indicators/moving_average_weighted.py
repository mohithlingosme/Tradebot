"""
Weighted Moving Average implementation.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Sequence

from .utils import wma


@dataclass
class MovingAverageWeighted:
    """Linear-weighted moving average."""

    period: int = 20

    def calculate(self, close: Sequence[float]) -> Optional[float]:
        return wma(close, self.period)

    def calculate_series(self, close: Sequence[float]) -> List[Optional[float]]:
        values: List[Optional[float]] = []
        for i in range(len(close)):
            values.append(wma(close[: i + 1], self.period))
        return values
