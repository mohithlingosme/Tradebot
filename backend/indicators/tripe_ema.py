"""
Triple Exponential Moving Average (TEMA).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Sequence

import numpy as np

from .utils import ema_series, ensure_length


@dataclass
class TripeEMA:
    """Triple-smoothed EMA (commonly called TEMA)."""

    period: int = 20

    def calculate(self, close: Sequence[float]) -> Optional[float]:
        if not ensure_length(close, self.period):
            return None
        value = self.calculate_series(close)[-1]
        return value

    def calculate_series(self, close: Sequence[float]) -> List[Optional[float]]:
        ema1 = ema_series(close, self.period)
        ema2 = ema_series(ema1, self.period)
        ema3 = ema_series(ema2, self.period)
        tema = 3 * ema1 - 3 * ema2 + ema3
        output: List[Optional[float]] = []
        for val in tema:
            if np.isnan(val):
                output.append(None)
            else:
                output.append(float(val))
        return output
