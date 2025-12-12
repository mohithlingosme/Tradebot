"""
True Strength Index Indicator

Double smoothed momentum oscillator.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Sequence

import numpy as np


@dataclass
class TrueStrengthIndex:
    """True Strength Index indicator."""

    short_period: int = 25
    long_period: int = 13

    def calculate(self, close: Sequence[float]) -> Optional[float]:
        """Return the TSI value for the latest period."""
        if len(close) < self.short_period + self.long_period:
            return None

        # Calculate momentum
        momentum = np.diff(close[-self.short_period - self.long_period:])

        # Double smooth momentum
        ema1 = self._ema(momentum, self.long_period)
        ema2 = self._ema([ema1], self.short_period)

        # Double smooth absolute momentum
        abs_momentum = np.abs(momentum)
        abs_ema1 = self._ema(abs_momentum, self.long_period)
        abs_ema2 = self._ema([abs_ema1], self.short_period)

        if abs_ema2 == 0:
            return 0.0

        tsi = 100 * (ema2 / abs_ema2)

        return float(tsi)

    def calculate_series(self, close: Sequence[float]) -> List[Optional[float]]:
        """Return TSI series."""
        tsi = []
        for i in range(len(close)):
            if i < self.short_period + self.long_period - 1:
                tsi.append(None)
            else:
                momentum = np.diff(close[i - self.short_period - self.long_period + 1 : i + 1])
                ema1 = self._ema(momentum, self.long_period)
                ema2 = self._ema([ema1], self.short_period)

                abs_momentum = np.abs(momentum)
                abs_ema1 = self._ema(abs_momentum, self.long_period)
                abs_ema2 = self._ema([abs_ema1], self.short_period)

                if abs_ema2 == 0:
                    tsi.append(0.0)
                else:
                    tsi_val = 100 * (ema2 / abs_ema2)
                    tsi.append(float(tsi_val))
        return tsi

    def _ema(self, data: Sequence[float], period: int) -> float:
        """Calculate EMA."""
        if len(data) < period:
            return np.mean(data)
        weights = np.exp(np.linspace(-1., 0., len(data)))
        weights /= weights.sum()
        return np.convolve(data, weights, mode='valid')[-1]
