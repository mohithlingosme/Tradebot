"""
Rate of Change Indicator

Measures the percentage change in price over a specified period.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Sequence


@dataclass
class RateOfChange:
    """Rate of Change indicator."""

    period: int = 14

    def calculate(self, close: Sequence[float]) -> Optional[float]:
        """Return the ROC value for the latest period."""
        if len(close) < self.period + 1:
            return None
        roc = ((close[-1] - close[-self.period - 1]) / close[-self.period - 1]) * 100
        return float(roc)

    def calculate_series(self, close: Sequence[float]) -> List[Optional[float]]:
        """Return ROC series."""
        roc = []
        for i in range(len(close)):
            if i < self.period:
                roc.append(None)
            else:
                change = ((close[i] - close[i - self.period]) / close[i - self.period]) * 100
                roc.append(float(change))
        return roc
