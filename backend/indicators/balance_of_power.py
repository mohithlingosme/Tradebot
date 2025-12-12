"""
Balance of Power Indicator

Measures the strength of buyers vs sellers.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Sequence


@dataclass
class BalanceOfPower:
    """Balance of Power indicator."""

    def calculate(self, open_prices: Sequence[float], high: Sequence[float], low: Sequence[float], close: Sequence[float]) -> Optional[float]:
        """Return the BOP value for the latest period."""
        if len(open_prices) == 0 or len(high) == 0 or len(low) == 0 or len(close) == 0:
            return None

        # BOP = (Close - Open) / (High - Low)
        if high[-1] == low[-1]:
            return 0.0

        bop = (close[-1] - open_prices[-1]) / (high[-1] - low[-1])

        return float(bop)

    def calculate_series(self, open_prices: Sequence[float], high: Sequence[float], low: Sequence[float], close: Sequence[float]) -> List[Optional[float]]:
        """Return BOP series."""
        if len(open_prices) != len(high) or len(high) != len(low) or len(low) != len(close):
            return []
        bop = []
        for i in range(len(close)):
            if high[i] == low[i]:
                bop.append(0.0)
            else:
                bop_val = (close[i] - open_prices[i]) / (high[i] - low[i])
                bop.append(float(bop_val))
        return bop
