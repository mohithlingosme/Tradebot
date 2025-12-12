"""
Open Interest indicator.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Sequence


@dataclass
class OpenInterestIndicator:
    """Track both the absolute open interest and its change."""

    def calculate(self, open_interest: Sequence[float]) -> Optional[float]:
        if not open_interest:
            return None
        return float(open_interest[-1])

    def calculate_series(self, open_interest: Sequence[float]) -> List[Optional[float]]:
        return [float(value) for value in open_interest]

    def delta_series(self, open_interest: Sequence[float]) -> List[Optional[float]]:
        if len(open_interest) < 2:
            return [None] * len(open_interest)
        output: List[Optional[float]] = [None]
        for i in range(1, len(open_interest)):
            output.append(float(open_interest[i] - open_interest[i - 1]))
        return output
