"""
Multi-time-period chart helper.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence


@dataclass
class MultiTimePeriodCharts:
    """Compute performance snapshots across multiple time horizons."""

    periods: List[int] = field(default_factory=lambda: [5, 15, 60, 120])

    def calculate(self, close: Sequence[float]) -> Optional[Dict[int, float]]:
        if len(close) < min(self.periods):
            return None
        values = {}
        for period in self.periods:
            if len(close) > period and close[-period] != 0:
                values[period] = (close[-1] / close[-period]) - 1.0
        return values or None

    def calculate_series(self, close: Sequence[float]) -> List[Optional[Dict[int, float]]]:
        return [self.calculate(close[: i + 1]) for i in range(len(close))]
