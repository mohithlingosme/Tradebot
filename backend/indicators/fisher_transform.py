"""
Fisher Transform Indicator

Normalizes asset prices to identify price reversals.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Sequence

import numpy as np


@dataclass
class FisherTransform:
    """Fisher Transform indicator."""

    period: int = 10

    def calculate(self, high: Sequence[float], low: Sequence[float]) -> Optional[float]:
        """Return the Fisher Transform value for the latest period."""
        if len(high) != len(low) or len(high) < self.period:
            return None

        # Calculate median price
        median = (np.array(high[-self.period:]) + np.array(low[-self.period:])) / 2

        # Normalize
        max_val = np.max(median)
        min_val = np.min(median)
        if max_val == min_val:
            return 0.0

        normalized = 2 * ((median[-1] - min_val) / (max_val - min_val)) - 1

        # Fisher Transform
        fisher = 0.5 * np.log((1 + normalized) / (1 - normalized))

        return float(fisher)

    def calculate_series(self, high: Sequence[float], low: Sequence[float]) -> List[Optional[float]]:
        """Return Fisher Transform series."""
        if len(high) != len(low):
            return []
        fisher = []
        for i in range(len(high)):
            if i < self.period - 1:
                fisher.append(None)
            else:
                median = (np.array(high[i - self.period + 1 : i + 1]) + np.array(low[i - self.period + 1 : i + 1])) / 2
                max_val = np.max(median)
                min_val = np.min(median)
                if max_val == min_val:
                    fisher.append(0.0)
                else:
                    normalized = 2 * ((median[-1] - min_val) / (max_val - min_val)) - 1
                    fisher_val = 0.5 * np.log((1 + normalized) / (1 - normalized))
                    fisher.append(float(fisher_val))
        return fisher
