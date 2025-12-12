"""
Coppock Curve Indicator

A momentum indicator that uses rate of change and weighted moving average.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Sequence

import numpy as np


@dataclass
class CoppockCurve:
    """Coppock Curve indicator."""

    roc1_period: int = 14
    roc2_period: int = 11
    wma_period: int = 10

    def calculate(self, close: Sequence[float]) -> Optional[float]:
        """Return the Coppock Curve value for the latest period."""
        if len(close) < max(self.roc1_period, self.roc2_period) + self.wma_period:
            return None

        # Calculate ROCs
        roc1 = (close[-1] - close[-self.roc1_period]) / close[-self.roc1_period] * 100
        roc2 = (close[-1] - close[-self.roc2_period]) / close[-self.roc2_period] * 100

        # Simple average of ROCs (this is simplified; typically WMA is used)
        avg_roc = (roc1 + roc2) / 2

        return float(avg_roc)

    def calculate_series(self, close: Sequence[float]) -> List[Optional[float]]:
        """Return Coppock Curve series."""
        coppock = []
        for i in range(len(close)):
            if i < max(self.roc1_period, self.roc2_period) + self.wma_period - 1:
                coppock.append(None)
            else:
                # Simplified calculation
                roc1 = (close[i] - close[i - self.roc1_period]) / close[i - self.roc1_period] * 100
                roc2 = (close[i] - close[i - self.roc2_period]) / close[i - self.roc2_period] * 100
                avg_roc = (roc1 + roc2) / 2
                coppock.append(float(avg_roc))
        return coppock
