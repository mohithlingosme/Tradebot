"""
Rank Correlation Index (RCI).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Sequence


def _rci(values: Sequence[float]) -> float:
    n = len(values)
    sorted_values = sorted(((v, idx) for idx, v in enumerate(values)), key=lambda x: x[0])
    ranks = {original_idx: rank for rank, (_, original_idx) in enumerate(sorted_values)}
    d_sum = 0
    for time_rank, (_, original_idx) in enumerate(sorted(sorted_values, key=lambda x: x[1])):
        diff = time_rank - ranks[original_idx]
        d_sum += diff * diff
    return (1 - (6 * d_sum) / (n * (n * n - 1))) * 100


@dataclass
class RankCorrelationIndex:
    """Compute the RCI over a rolling window."""

    period: int = 9

    def calculate(self, close: Sequence[float]) -> Optional[float]:
        if len(close) < self.period:
            return None
        return _rci(close[-self.period :])

    def calculate_series(self, close: Sequence[float]) -> List[Optional[float]]:
        values: List[Optional[float]] = []
        for i in range(len(close)):
            if i + 1 < self.period:
                values.append(None)
            else:
                values.append(_rci(close[i - self.period + 1 : i + 1]))
        return values
