"""
Double Exponential Moving Average (DEMA).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Sequence

import numpy as np

from .utils import ema_series, ensure_length


@dataclass
class DoubleEMS:
    """Classic DEMA smoothing."""

    period: int = 20

    def calculate(self, close: Sequence[float]) -> Optional[float]:
        if not ensure_length(close, self.period):
            return None
        ema = ema_series(close, self.period)
        ema_of_ema = ema_series(ema, self.period)
        value = 2 * ema[-1] - ema_of_ema[-1]
        return float(value)

    def calculate_series(self, close: Sequence[float]) -> List[Optional[float]]:
        ema = ema_series(close, self.period)
        ema_of_ema = ema_series(ema, self.period)
        dema = 2 * ema - ema_of_ema
        output: List[Optional[float]] = []
        for idx, val in enumerate(dema):
            if np.isnan(val):
                output.append(None)
            else:
                output.append(float(val))
        return output
