"""
Relative Vigor Index Indicator

Compares the closing price to the opening price to identify the direction of price movement.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Sequence

import numpy as np


@dataclass
class RelativeVigorIndex:
    """Relative Vigor Index indicator."""

    period: int = 10

    def calculate(self, open_prices: Sequence[float], close: Sequence[float]) -> Optional[float]:
        """Return the RVI value for the latest period."""
        if len(open_prices) < self.period or len(close) < self.period:
            return None

        # Calculate RVI
        numerator = np.mean(close[-self.period:] - open_prices[-self.period:])
        denominator = np.mean(open_prices[-self.period:] - close[-self.period:])
        if denominator == 0:
            return 0.0
        rvi = numerator / denominator

        return float(rvi)

    def calculate_series(self, open_prices: Sequence[float], close: Sequence[float]) -> List[Optional[float]]:
        """Return RVI series."""
        if len(open_prices) != len(close):
            return []
        rvi = []
        for i in range(len(close)):
            if i < self.period - 1:
                rvi.append(None)
            else:
                num = np.mean(close[i - self.period + 1 : i + 1] - open_prices[i - self.period + 1 : i + 1])
                den = np.mean(open_prices[i - self.period + 1 : i + 1] - close[i - self.period + 1 : i + 1])
                if den == 0:
                    rvi.append(0.0)
                else:
                    rvi.append(float(num / den))
        return rvi
