"""
Advance Decline Ratio Indicator

Calculates the ratio of advancing stocks to declining stocks.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Sequence


@dataclass
class AdvanceDeclineRatio:
    """Advance Decline Ratio indicator."""

    def calculate(self, advancing: Sequence[float], declining: Sequence[float]) -> Optional[float]:
        """Return the ADR value for the latest period."""
        if len(advancing) != len(declining) or len(advancing) == 0 or declining[-1] == 0:
            return None
        return float(advancing[-1] / declining[-1])

    def calculate_series(self, advancing: Sequence[float], declining: Sequence[float]) -> List[Optional[float]]:
        """Return ADR series."""
        if len(advancing) != len(declining):
            return []
        adr = []
        for i in range(len(advancing)):
            if declining[i] == 0:
                adr.append(None)
            else:
                adr.append(float(advancing[i] / declining[i]))
        return adr
