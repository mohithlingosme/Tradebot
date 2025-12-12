"""
Stochastic Momentum Index Indicator

Combines momentum and stochastic oscillator concepts.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Sequence

import numpy as np


@dataclass
class StochasticMomentumIndex:
    """Stochastic Momentum Index indicator."""

    k_period: int = 14
    smooth_k: int = 3
    d_period: int = 3

    def calculate(self, high: Sequence[float], low: Sequence[float], close: Sequence[float]) -> Optional[float]:
        """Return the SMI value for the latest period."""
        if len(high) < self.k_period or len(low) < self.k_period or len(close) < self.k_period:
            return None

        # Calculate highest high and lowest low
        hh = np.max(high[-self.k_period:])
        ll = np.min(low[-self.k_period:])

        if hh == ll:
            return 0.0

        # Calculate SMI
        m = (close[-1] - (hh + ll) / 2) / ((hh - ll) / 2) * 100

        return float(m)

    def calculate_series(self, high: Sequence[float], low: Sequence[float], close: Sequence[float]) -> List[Optional[float]]:
        """Return SMI series."""
        if len(high) != len(low) or len(low) != len(close):
            return []
        smi = []
        for i in range(len(close)):
            if i < self.k_period - 1:
                smi.append(None)
            else:
                hh = np.max(high[i - self.k_period + 1 : i + 1])
                ll = np.min(low[i - self.k_period + 1 : i + 1])
                if hh == ll:
                    smi.append(0.0)
                else:
                    m = (close[i] - (hh + ll) / 2) / ((hh - ll) / 2) * 100
                    smi.append(float(m))
        return smi
