"""
Mass Index Indicator

Identifies reversals by measuring range expansion.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Sequence

import numpy as np


@dataclass
class MassIndex:
    """Mass Index indicator."""

    period: int = 25
    ema_period: int = 9

    def calculate(self, high: Sequence[float], low: Sequence[float]) -> Optional[float]:
        """Return the Mass Index value for the latest period."""
        if len(high) < self.period or len(low) < self.period:
            return None

        # Calculate single EMA of range
        ranges = np.array(high[-self.period:]) - np.array(low[-self.period:])
        ema1 = self._ema(ranges, self.ema_period)

        # Calculate double EMA
        ema2 = self._ema([ema1], self.ema_period)

        # Mass Index
        if ema2 == 0:
            return 0.0

        mass_index = ema1 / ema2

        return float(mass_index)

    def calculate_series(self, high: Sequence[float], low: Sequence[float]) -> List[Optional[float]]:
        """Return Mass Index series."""
        if len(high) != len(low):
            return []
        mass_values = []
        for i in range(len(high)):
            if i < self.period - 1:
                mass_values.append(None)
            else:
                ranges = np.array(high[i - self.period + 1 : i + 1]) - np.array(low[i - self.period + 1 : i + 1])
                ema1 = self._ema(ranges, self.ema_period)
                ema2 = self._ema([ema1], self.ema_period)
                if ema2 == 0:
                    mass_values.append(0.0)
                else:
                    mass_index = ema1 / ema2
                    mass_values.append(float(mass_index))
        return mass_values

    def _ema(self, data: Sequence[float], period: int) -> float:
        """Calculate EMA."""
        if len(data) < period:
            return np.mean(data)
        weights = np.exp(np.linspace(-1., 0., len(data)))
        weights /= weights.sum()
        return np.convolve(data, weights, mode='valid')[-1]
