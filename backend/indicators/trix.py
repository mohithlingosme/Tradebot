"""
TRIX (Triple Exponential Oscillator).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Sequence

import numpy as np

from .utils import ema_series, ensure_length


@dataclass
class TRIX:
    """Return the percentage change of the triple-smoothed EMA."""

    period: int = 15

    def calculate(self, close: Sequence[float]) -> Optional[float]:
        values = self.calculate_series(close)
        return values[-1]

    def calculate_series(self, close: Sequence[float]) -> List[Optional[float]]:
        if not ensure_length(close, self.period + 1):
            return [None] * len(close)
        ema1 = ema_series(close, self.period)
        ema2 = ema_series(ema1, self.period)
        ema3 = ema_series(ema2, self.period)
        trix_raw = np.full(len(ema3), np.nan, dtype=float)
        for i in range(1, len(ema3)):
            prev = ema3[i - 1]
            if prev == 0:
                continue
            trix_raw[i] = 100.0 * (ema3[i] - prev) / prev
        result: List[Optional[float]] = []
        for val in trix_raw:
            result.append(float(val) if not np.isnan(val) else None)
        return result
