"""
Least Squares Moving Average (LSMA), also known as the linear regression moving average.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Sequence

import numpy as np

from .utils import linear_regression


@dataclass
class LeastSquaresMovingAverage:
    """Regression-based moving average."""

    period: int = 25

    def calculate(self, close: Sequence[float]) -> Optional[float]:
        series = self.calculate_series(close)
        return series[-1] if series else None

    def calculate_series(self, close: Sequence[float]) -> List[Optional[float]]:
        line, _ = linear_regression(close, self.period)
        output: List[Optional[float]] = []
        for value in line:
            if np.isnan(value):
                output.append(None)
            else:
                output.append(float(value))
        return output
