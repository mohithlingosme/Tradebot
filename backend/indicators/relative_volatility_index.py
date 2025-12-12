"""
Relative Volatility Index Indicator

Measures the direction of volatility.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Sequence

import numpy as np


@dataclass
class RelativeVolatilityIndex:
    """Relative Volatility Index indicator."""

    period: int = 14

    def calculate(self, close: Sequence[float]) -> Optional[float]:
        """Return the RVI value for the latest period."""
        if len(close) < self.period + 1:
            return None

        # Calculate price changes
        changes = np.diff(close[-self.period - 1:])

        # Separate up and down changes
        up_changes = np.where(changes > 0, changes, 0)
        down_changes = np.where(changes < 0, -changes, 0)

        # Calculate standard deviations
        up_std = np.std(up_changes)
        down_std = np.std(down_changes)

        if up_std + down_std == 0:
            return 50.0

        rvi = 100 * (up_std / (up_std + down_std))

        return float(rvi)

    def calculate_series(self, close: Sequence[float]) -> List[Optional[float]]:
        """Return RVI series."""
        rvi = []
        for i in range(len(close)):
            if i < self.period:
                rvi.append(None)
            else:
                changes = np.diff(close[i - self.period : i + 1])
                up_changes = np.where(changes > 0, changes, 0)
                down_changes = np.where(changes < 0, -changes, 0)
                up_std = np.std(up_changes)
                down_std = np.std(down_changes)
                if up_std + down_std == 0:
                    rvi.append(50.0)
                else:
                    rvi_val = 100 * (up_std / (up_std + down_std))
                    rvi.append(float(rvi_val))
        return rvi
