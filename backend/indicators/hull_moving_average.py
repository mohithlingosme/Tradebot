"""
Hull Moving Average (HMA).
"""

from __future__ import annotations

from dataclasses import dataclass
from math import sqrt
from typing import List, Optional, Sequence

import numpy as np

from .utils import wma


@dataclass
class HullMovingAverage:
    """Smooth yet responsive moving average."""

    period: int = 21

    def calculate(self, close: Sequence[float]) -> Optional[float]:
        values = self.calculate_series(close)
        return values[-1] if values else None

    def calculate_series(self, close: Sequence[float]) -> List[Optional[float]]:
        arr = list(float(v) for v in close)
        if not arr:
            return []
        half_period = max(1, self.period // 2)
        sqrt_period = max(1, int(sqrt(self.period)))
        wma_half: List[Optional[float]] = []
        wma_full: List[Optional[float]] = []
        for i in range(len(arr)):
            wma_half.append(wma(arr[: i + 1], half_period))
            wma_full.append(wma(arr[: i + 1], self.period))
        diff = []
        for wh, wf in zip(wma_half, wma_full):
            if wh is None or wf is None:
                diff.append(None)
            else:
                diff.append(2 * wh - wf)
        hma: List[Optional[float]] = []
        for i in range(len(arr)):
            series = [d for d in diff[: i + 1] if d is not None]
            hma.append(wma(series, sqrt_period) if series else None)
        return hma
