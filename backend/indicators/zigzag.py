"""
Zig Zag Indicator

Filters out market noise to show significant price movements.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Sequence

import numpy as np


@dataclass
class ZigZag:
    """Zig Zag indicator."""

    deviation: float = 5.0  # Percentage deviation

    def calculate(self, high: Sequence[float], low: Sequence[float]) -> Optional[List[float]]:
        """Return the ZigZag values for the latest period."""
        if len(high) < 3 or len(low) < 3:
            return None

        # Simplified ZigZag calculation
        # In practice, this requires tracking pivot points
        # For now, return a basic approximation
        return [float(high[-1]), float(low[-1])]

    def calculate_series(self, high: Sequence[float], low: Sequence[float]) -> List[Optional[List[float]]]:
        """Return ZigZag series."""
        if len(high) != len(low):
            return []
        zigzag = []
        last_pivot = high[0]
        trend_up = True

        for i in range(len(high)):
            current_high = high[i]
            current_low = low[i]

            if trend_up:
                if current_low < last_pivot * (1 - self.deviation / 100):
                    # Switch to downtrend
                    zigzag.append([last_pivot, current_low])
                    last_pivot = current_low
                    trend_up = False
                else:
                    zigzag.append([last_pivot, current_high])
            else:
                if current_high > last_pivot * (1 + self.deviation / 100):
                    # Switch to uptrend
                    zigzag.append([current_high, last_pivot])
                    last_pivot = current_high
                    trend_up = True
                else:
                    zigzag.append([current_high, last_pivot])

        return zigzag
