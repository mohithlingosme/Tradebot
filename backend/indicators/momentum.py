"""
Momentum Indicator

Measures the rate of change in price over a specified period.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Sequence


@dataclass
class Momentum:
    """Momentum indicator."""

    period: int = 14

    def calculate(self, close: Sequence[float]) -> Optional[float]:
        """Return the momentum value for the latest period."""
        if len(close) < self.period + 1:
            return None
        return float(close[-1] - close[-self.period - 1])

    def calculate_series(self, close: Sequence[float]) -> List[Optional[float]]:
        """Return momentum series."""
        momentum = []
        for i in range(len(close)):
            if i < self.period:
                momentum.append(None)
            else:
                mom = close[i] - close[i - self.period]
                momentum.append(float(mom))
        return momentum
