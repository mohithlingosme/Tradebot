"""
Median price indicator.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Sequence

import numpy as np


@dataclass
class MedianPrice:
    """Return (high + low) / 2 to highlight the midpoint of each bar."""

    def calculate(self, high: Sequence[float], low: Sequence[float]) -> Optional[float]:
        if not high or not low or len(high) != len(low):
            return None
        return float((high[-1] + low[-1]) / 2.0)

    def calculate_series(self, high: Sequence[float], low: Sequence[float]) -> List[Optional[float]]:
        if len(high) != len(low):
            return []
        high_arr = np.asarray(high, dtype=float)
        low_arr = np.asarray(low, dtype=float)
        midpoint = (high_arr + low_arr) / 2.0
        return midpoint.astype(float).tolist()
