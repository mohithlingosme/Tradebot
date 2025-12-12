"""
Historical Volatility Indicator

Measures the standard deviation of price changes over a period.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Sequence

import numpy as np


@dataclass
class HistoricalVolatility:
    """Historical Volatility indicator."""

    period: int = 20

    def calculate(self, close: Sequence[float]) -> Optional[float]:
        """Return the historical volatility for the latest period."""
        if len(close) < self.period + 1:
            return None

        # Calculate returns
        returns = np.diff(np.log(close[-self.period - 1:]))

        # Annualized volatility
        volatility = np.std(returns) * np.sqrt(252)  # Assuming daily data

        return float(volatility)

    def calculate_series(self, close: Sequence[float]) -> List[Optional[float]]:
        """Return historical volatility series."""
        volatilities = []
        for i in range(len(close)):
            if i < self.period:
                volatilities.append(None)
            else:
                returns = np.diff(np.log(close[i - self.period : i + 1]))
                vol = np.std(returns) * np.sqrt(252)
                volatilities.append(float(vol))
        return volatilities
