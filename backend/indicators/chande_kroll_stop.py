"""
Chande Kroll Stop implementation.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence

import numpy as np

from .utils import rolling_high, rolling_low, sma_series, true_range


@dataclass
class ChandeKrollStop:
    """Volatility-based trailing stop."""

    period: int = 20
    atr_period: int = 10
    multiplier: float = 1.5

    def calculate(
        self,
        high: Sequence[float],
        low: Sequence[float],
        close: Sequence[float],
    ) -> Optional[Dict[str, float]]:
        values = self.calculate_series(high, low, close)
        return values[-1] if values else None

    def calculate_series(
        self,
        high: Sequence[float],
        low: Sequence[float],
        close: Sequence[float],
    ) -> List[Optional[Dict[str, float]]]:
        if not (len(high) == len(low) == len(close)):
            return []
        tr = true_range(high, low, close)
        atr = sma_series(tr, self.atr_period)
        highest = rolling_high(high, self.period)
        lowest = rolling_low(low, self.period)
        output: List[Optional[Dict[str, float]]] = []
        for h, l, a in zip(highest, lowest, atr):
            if np.isnan(h) or np.isnan(l) or np.isnan(a):
                output.append(None)
            else:
                output.append(
                    {
                        "long_stop": float(l + self.multiplier * a),
                        "short_stop": float(h - self.multiplier * a),
                    }
                )
        return output
