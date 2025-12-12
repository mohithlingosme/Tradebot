"""
Linear Regression Channel.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence

import numpy as np

from .utils import linear_regression


@dataclass
class LinearRegressionChannel:
    """Regression channel comprised of a center line plus ±1 standard deviation."""

    period: int = 100

    def calculate(self, close: Sequence[float]) -> Optional[Dict[str, float]]:
        values = self.calculate_series(close)
        return values[-1] if values else None

    def calculate_series(self, close: Sequence[float]) -> List[Optional[Dict[str, float]]]:
        line, slope = linear_regression(close, self.period)
        arr = np.asarray(close, dtype=float)
        output: List[Optional[Dict[str, float]]] = []
        for idx in range(len(arr)):
            if np.isnan(line[idx]):
                output.append(None)
                continue
            window = arr[idx - self.period + 1 : idx + 1]
            center = line[idx]
            slope_val = slope[idx] if not np.isnan(slope[idx]) else 0.0
            regression_line = np.linspace(center - slope_val * (self.period - 1), center, self.period)
            deviations = window - regression_line
            std = float(np.std(deviations))
            output.append({"center": float(center), "upper": float(center + std), "lower": float(center - std)})
        return output
