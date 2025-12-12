"""
Smoothed Moving Average (SMMA), sometimes referred to as Wilder's moving average.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Sequence

import numpy as np

from .utils import ensure_length, sma


@dataclass
class SmoothedMovingAverage:
    """SMMA equivalent to the moving average used inside RSI/ADX calculations."""

    period: int = 14

    def calculate(self, close: Sequence[float]) -> Optional[float]:
        series = self.calculate_series(close)
        return series[-1]

    def calculate_series(self, close: Sequence[float]) -> List[Optional[float]]:
        arr = list(float(v) for v in close)
        if not arr:
            return []
        smma: List[Optional[float]] = [None] * len(arr)
        initial = sma(arr, self.period)
        if initial is None:
            return smma
        smma[self.period - 1] = initial
        prev = initial
        for i in range(self.period, len(arr)):
            prev = (prev * (self.period - 1) + arr[i]) / self.period
            smma[i] = prev
        return smma
