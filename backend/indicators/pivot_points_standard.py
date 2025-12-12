"""
Standard floor-trader pivot points.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence


@dataclass
class PivotPointsStandard:
    """Calculate classic pivot, resistance, and support levels."""

    def calculate(self, high: Sequence[float], low: Sequence[float], close: Sequence[float]) -> Optional[Dict[str, float]]:
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
        pivots: List[Optional[Dict[str, float]]] = [None]
        for idx in range(1, len(close)):
            prev_high = high[idx - 1]
            prev_low = low[idx - 1]
            prev_close = close[idx - 1]
            pivot = (prev_high + prev_low + prev_close) / 3.0
            range_val = prev_high - prev_low
            pivots.append(
                {
                    "pivot": pivot,
                    "r1": pivot + range_val,
                    "s1": pivot - range_val,
                    "r2": pivot + 2 * range_val,
                    "s2": pivot - 2 * range_val,
                }
            )
        return pivots
