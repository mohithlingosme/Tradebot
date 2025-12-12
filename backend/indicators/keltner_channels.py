"""
Keltner Channels Indicator

Channels based on ATR around an EMA.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence

import numpy as np


@dataclass
class KeltnerChannels:
    """Keltner Channels indicator."""

    period: int = 20
    atr_period: int = 10
    multiplier: float = 2.0

    def calculate(self, high: Sequence[float], low: Sequence[float], close: Sequence[float]) -> Optional[Dict[str, float]]:
        """Return the Keltner Channels for the latest period."""
        if len(high) < self.period or len(low) < self.period or len(close) < self.period:
            return None

        # Calculate EMA of close
        ema = self._ema(close[-self.period:], self.period)

        # Calculate ATR
        atr = self._calculate_atr(high[-self.atr_period:], low[-self.atr_period:], close[-self.atr_period:])

        # Upper and lower channels
        upper = ema + (self.multiplier * atr)
        lower = ema - (self.multiplier * atr)

        return {
            'upper': float(upper),
            'middle': float(ema),
            'lower': float(lower)
        }

    def calculate_series(self, high: Sequence[float], low: Sequence[float], close: Sequence[float]) -> List[Optional[Dict[str, float]]]:
        """Return Keltner Channels series."""
        if len(high) != len(low) or len(low) != len(close):
            return []
        channels = []
        for i in range(len(close)):
            if i < max(self.period, self.atr_period) - 1:
                channels.append(None)
            else:
                ema = self._ema(close[i - self.period + 1 : i + 1], self.period)
                atr = self._calculate_atr(high[i - self.atr_period + 1 : i + 1], low[i - self.atr_period + 1 : i + 1], close[i - self.atr_period + 1 : i + 1])
                upper = ema + (self.multiplier * atr)
                lower = ema - (self.multiplier * atr)
                channels.append({
                    'upper': float(upper),
                    'middle': float(ema),
                    'lower': float(lower)
                })
        return channels

    def _ema(self, data: Sequence[float], period: int) -> float:
        """Calculate EMA."""
        if len(data) < period:
            return np.mean(data)
        weights = np.exp(np.linspace(-1., 0., len(data)))
        weights /= weights.sum()
        return np.convolve(data, weights, mode='valid')[-1]

    def _calculate_atr(self, high: Sequence[float], low: Sequence[float], close: Sequence[float]) -> float:
        """Calculate Average True Range."""
        tr = []
        for i in range(1, len(close)):
            tr1 = high[i] - low[i]
            tr2 = abs(high[i] - close[i-1])
            tr3 = abs(low[i] - close[i-1])
            tr.append(max(tr1, tr2, tr3))
        return np.mean(tr)
