"""
Supertrend Indicator

Trend-following indicator that combines ATR and price action.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Sequence

import numpy as np


@dataclass
class Supertrend:
    """Supertrend indicator."""

    period: int = 10
    multiplier: float = 3.0

    def calculate(self, high: Sequence[float], low: Sequence[float], close: Sequence[float]) -> Optional[float]:
        """Return the Supertrend value for the latest period."""
        if len(high) < self.period or len(low) < self.period or len(close) < self.period:
            return None

        # Calculate ATR
        atr = self._calculate_atr(high[-self.period:], low[-self.period:], close[-self.period:])

        # Calculate basic upper and lower bands
        hl2 = (high[-1] + low[-1]) / 2
        upper_band = hl2 + (self.multiplier * atr)
        lower_band = hl2 - (self.multiplier * atr)

        # Determine trend (simplified)
        if close[-1] > upper_band:
            return float(lower_band)  # Bullish
        else:
            return float(upper_band)  # Bearish

    def calculate_series(self, high: Sequence[float], low: Sequence[float], close: Sequence[float]) -> List[Optional[float]]:
        """Return Supertrend series."""
        if len(high) != len(low) or len(low) != len(close):
            return []
        supertrend = []
        for i in range(len(close)):
            if i < self.period - 1:
                supertrend.append(None)
            else:
                atr = self._calculate_atr(high[i - self.period + 1 : i + 1], low[i - self.period + 1 : i + 1], close[i - self.period + 1 : i + 1])
                hl2 = (high[i] + low[i]) / 2
                upper_band = hl2 + (self.multiplier * atr)
                lower_band = hl2 - (self.multiplier * atr)
                if close[i] > upper_band:
                    supertrend.append(float(lower_band))
                else:
                    supertrend.append(float(upper_band))
        return supertrend

    def _calculate_atr(self, high: Sequence[float], low: Sequence[float], close: Sequence[float]) -> float:
        """Calculate Average True Range."""
        tr = []
        for i in range(1, len(close)):
            tr1 = high[i] - low[i]
            tr2 = abs(high[i] - close[i-1])
            tr3 = abs(low[i] - close[i-1])
            tr.append(max(tr1, tr2, tr3))
        return np.mean(tr)
