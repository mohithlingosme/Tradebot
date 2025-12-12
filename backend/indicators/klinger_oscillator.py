"""
Klinger Oscillator Indicator

Volume-based oscillator that combines volume and price action.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Sequence

import numpy as np


@dataclass
class KlingerOscillator:
    """Klinger Oscillator indicator."""

    fast_period: int = 34
    slow_period: int = 55
    signal_period: int = 13

    def calculate(self, high: Sequence[float], low: Sequence[float], close: Sequence[float], volume: Sequence[float]) -> Optional[float]:
        """Return the Klinger Oscillator value for the latest period."""
        if len(high) < self.slow_period or len(low) < self.slow_period or len(close) < self.slow_period or len(volume) < self.slow_period:
            return None

        # Calculate Trend
        trend = []
        for i in range(1, len(close)):
            if close[i] > close[i-1]:
                trend.append(volume[i])
            elif close[i] < close[i-1]:
                trend.append(-volume[i])
            else:
                trend.append(0)

        # Fast EMA
        fast_ema = self._ema(trend[-self.fast_period:], self.fast_period)

        # Slow EMA
        slow_ema = self._ema(trend[-self.slow_period:], self.slow_period)

        # Klinger Oscillator
        klinger = fast_ema - slow_ema

        return float(klinger)

    def calculate_series(self, high: Sequence[float], low: Sequence[float], close: Sequence[float], volume: Sequence[float]) -> List[Optional[float]]:
        """Return Klinger Oscillator series."""
        klingers = []
        for i in range(len(close)):
            if i < self.slow_period:
                klingers.append(None)
            else:
                trend = []
                for j in range(1, i+1):
                    if close[j] > close[j-1]:
                        trend.append(volume[j])
                    elif close[j] < close[j-1]:
                        trend.append(-volume[j])
                    else:
                        trend.append(0)

                fast_ema = self._ema(trend[-self.fast_period:], self.fast_period)
                slow_ema = self._ema(trend[-self.slow_period:], self.slow_period)
                klinger = fast_ema - slow_ema
                klingers.append(float(klinger))
        return klingers

    def _ema(self, data: Sequence[float], period: int) -> float:
        """Calculate EMA."""
        data = np.array(data)
        weights = np.exp(np.linspace(-1., 0., period))
        weights /= weights.sum()
        return np.convolve(data, weights, mode='valid')[-1]
