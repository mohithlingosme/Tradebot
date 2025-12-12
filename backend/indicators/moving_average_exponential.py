"""
Exponential Moving Average wrapper.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Sequence

from .moving_average import EMA


@dataclass
class MovingAverageExponential:
    """Delegates to the EMA helper."""

    period: int = 20

    def _indicator(self) -> EMA:
        return EMA(period=self.period)

    def calculate(self, close: Sequence[float]) -> Optional[float]:
        return self._indicator().calculate(list(close))

    def calculate_series(self, close: Sequence[float]) -> List[Optional[float]]:
        return self._indicator().calculate_series(list(close))
