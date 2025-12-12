"""
Choppiness Index Indicator

Measures the trendiness or choppiness of the market.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Sequence

import numpy as np


@dataclass
class ChoppinessIndex:
    """Choppiness Index indicator."""

    period: int = 14

    def calculate(self, high: Sequence[float], low: Sequence[float], close: Sequence[float]) -> Optional[float]:
        """Return the Choppiness Index value for the latest period."""
        if len(high) < self.period or len(low) < self.period or len(close) < self.period:
            return None

        # Calculate true range
        tr = []
        for i in range(1, self.period):
            tr1 = high[-i] - low[-i]
            tr2 = abs(high[-i] - close[-i-1])
            tr3 = abs(low[-i] - close[-i-1])
            tr.append(max(tr1, tr2, tr3))

        # Sum of true ranges
        sum_tr = sum(tr)

        # Highest high and lowest low over period
        hh = max(high[-self.period:])
        ll = min(low[-self.period:])

        # Choppiness Index
        if sum_tr == 0:
            return 0.0

        ci = 100 * np.log10(sum_tr / (hh - ll)) / np.log10(self.period)

        return float(ci)

    def calculate_series(self, high: Sequence[float], low: Sequence[float], close: Sequence[float]) -> List[Optional[float]]:
        """Return Choppiness Index series."""
        if len(high) != len(low) or len(low) != len(close):
            return []
        ci_values = []
        for i in range(len(close)):
            if i < self.period - 1:
                ci_values.append(None)
            else:
                tr = []
                for j in range(1, self.period):
                    idx = i - j + 1
                    tr1 = high[idx] - low[idx]
                    tr2 = abs(high[idx] - close[idx-1]) if idx > 0 else tr1
                    tr3 = abs(low[idx] - close[idx-1]) if idx > 0 else tr1
                    tr.append(max(tr1, tr2, tr3))

                sum_tr = sum(tr)
                hh = max(high[i - self.period + 1 : i + 1])
                ll = min(low[i - self.period + 1 : i + 1])

                if sum_tr == 0 or hh == ll:
                    ci_values.append(0.0)
                else:
                    ci = 100 * np.log10(sum_tr / (hh - ll)) / np.log10(self.period)
                    ci_values.append(float(ci))
        return ci_values
