"""
Average Day Range Indicator

Calculates the average range of price movement over a period.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Sequence

import numpy as np


@dataclass
class AverageDayRange:
    """Average Day Range indicator."""

    period: int = 14

    def calculate(self, high: Sequence[float], low: Sequence[float]) -> Optional[float]:
        """Return the ADR value for the latest period."""
        if len(high) < self.period or len(low) < self.period:
            return None

        # Calculate daily ranges
        ranges = np.array(high[-self.period:]) - np.array(low[-self.period:])

        # Average range
        adr = np.mean(ranges)

        return float(adr)

    def calculate_series(self, high: Sequence[float], low: Sequence[float]) -> List[Optional[float]]:
        """Return ADR series."""
        if len(high) != len(low):
            return []
        adr = []
        for i in range(len(high)):
            if i < self.period - 1:
                adr.append(None)
            else:
                ranges = np.array(high[i - self.period + 1 : i + 1]) - np.array(low[i - self.period + 1 : i + 1])
                adr_val = np.mean(ranges)
                adr.append(float(adr_val))
        return adr
