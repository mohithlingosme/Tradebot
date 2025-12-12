"""
Advance Decline Line Indicator

Calculates the cumulative difference between advancing and declining stocks.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Sequence


@dataclass
class AdvanceDeclineLine:
    """Advance Decline Line indicator."""

    def calculate(self, advancing: Sequence[float], declining: Sequence[float]) -> Optional[float]:
        """Return the ADL value for the latest period."""
        if len(advancing) != len(declining) or len(advancing) == 0:
            return None
        return float(advancing[-1] - declining[-1])

    def calculate_series(self, advancing: Sequence[float], declining: Sequence[float]) -> List[Optional[float]]:
        """Return cumulative ADL series."""
        if len(advancing) != len(declining):
            return []
        adl = []
        cumulative = 0.0
        for i in range(len(advancing)):
            cumulative += advancing[i] - declining[i]
            adl.append(float(cumulative))
        return adl
