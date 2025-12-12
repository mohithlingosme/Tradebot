"""
Correlation Coefficient Indicator

Measures the correlation between two price series.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Sequence

import numpy as np


@dataclass
class CorrelationCoefficient:
    """Correlation Coefficient indicator."""

    period: int = 20

    def calculate(self, series1: Sequence[float], series2: Sequence[float]) -> Optional[float]:
        """Return the correlation coefficient for the latest period."""
        if len(series1) < self.period or len(series2) < self.period:
            return None

        # Calculate correlation
        corr = np.corrcoef(series1[-self.period:], series2[-self.period:])[0, 1]

        return float(corr)

    def calculate_series(self, series1: Sequence[float], series2: Sequence[float]) -> List[Optional[float]]:
        """Return correlation coefficient series."""
        if len(series1) != len(series2):
            return []
        correlations = []
        for i in range(len(series1)):
            if i < self.period - 1:
                correlations.append(None)
            else:
                corr = np.corrcoef(series1[i - self.period + 1 : i + 1], series2[i - self.period + 1 : i + 1])[0, 1]
                correlations.append(float(corr))
        return correlations
