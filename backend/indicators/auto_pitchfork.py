"""
Simplified automatic Andrews Pitchfork implementation.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional, Sequence

import numpy as np


@dataclass
class AutoPitchfork:
    """Derive three pivots from the lookback window and project fork lines."""

    lookback: int = 100

    def calculate(self, high: Sequence[float], low: Sequence[float], close: Sequence[float]) -> Optional[Dict[str, float]]:
        if not (len(high) == len(low) == len(close)):
            return None
        if len(close) < self.lookback:
            return None
        start = len(close) - self.lookback
        window_close = np.asarray(close[start:], dtype=float)
        window_high = np.asarray(high[start:], dtype=float)
        window_low = np.asarray(low[start:], dtype=float)
        idx_low = int(np.argmin(window_low)) + start
        idx_high = int(np.argmax(window_high)) + start
        idx_latest = len(close) - 1
        p0 = (idx_low, close[idx_low])
        p1 = (idx_high, close[idx_high])
        center_x = (p0[0] + p1[0]) / 2.0
        center_y = (p0[1] + p1[1]) / 2.0
        if idx_latest == center_x:
            return None
        slope = (close[idx_latest] - center_y) / (idx_latest - center_x)
        intercept = close[idx_latest] - slope * idx_latest
        upper_offset = abs(p1[1] - center_y)
        lower_offset = abs(center_y - p0[1])
        return {
            "median_slope": float(slope),
            "median_intercept": float(intercept),
            "upper_intercept": float(intercept + upper_offset),
            "lower_intercept": float(intercept - lower_offset),
        }
