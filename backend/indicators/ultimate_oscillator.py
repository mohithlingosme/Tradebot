"""
Ultimate Oscillator Indicator

Combines short, medium, and long-term buying pressure.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Sequence

import numpy as np


@dataclass
class UltimateOscillator:
    """Ultimate Oscillator indicator."""

    short_period: int = 7
    medium_period: int = 14
    long_period: int = 28

    def calculate(self, high: Sequence[float], low: Sequence[float], close: Sequence[float]) -> Optional[float]:
        """Return the Ultimate Oscillator value for the latest period."""
        if len(high) < self.long_period or len(low) < self.long_period or len(close) < self.long_period:
            return None

        # Calculate buying pressure
        bp = close[-1] - np.minimum(low[-1], close[-2] if len(close) > 1 else close[-1])

        # Calculate true ranges
        tr = np.maximum(high[-1] - low[-1],
                       np.maximum(abs(high[-1] - close[-2] if len(close) > 1 else 0),
                                 abs(low[-1] - close[-2] if len(close) > 1 else 0)))

        # Calculate averages (simplified)
        avg7 = bp / tr if tr != 0 else 0
        avg14 = bp / tr if tr != 0 else 0
        avg28 = bp / tr if tr != 0 else 0

        # Ultimate Oscillator
        uo = 100 * ((4 * avg7) + (2 * avg14) + avg28) / 7

        return float(uo)

    def calculate_series(self, high: Sequence[float], low: Sequence[float], close: Sequence[float]) -> List[Optional[float]]:
        """Return Ultimate Oscillator series."""
        if len(high) != len(low) or len(low) != len(close):
            return []
        uo = []
        for i in range(len(close)):
            if i < self.long_period - 1:
                uo.append(None)
            else:
                # Simplified calculation
                bp = close[i] - min(low[i], close[i-1] if i > 0 else close[i])
                tr = max(high[i] - low[i],
                        abs(high[i] - close[i-1] if i > 0 else 0),
                        abs(low[i] - close[i-1] if i > 0 else 0))
                avg7 = bp / tr if tr != 0 else 0
                avg14 = bp / tr if tr != 0 else 0
                avg28 = bp / tr if tr != 0 else 0
                uo_val = 100 * ((4 * avg7) + (2 * avg14) + avg28) / 7
                uo.append(float(uo_val))
        return uo
