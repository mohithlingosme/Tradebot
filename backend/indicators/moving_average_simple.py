"""
Simple Moving Average wrapper.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Sequence

from .moving_average import SMA


@dataclass
class MovingAverageSimple:
    """Thin convenience wrapper around :class:`backend.indicators.moving_average.SMA`."""

    period: int = 20

    def _indicator(self) -> SMA:
        return SMA(period=self.period)

    def calculate(self, close: Sequence[float]) -> Optional[float]:
        return self._indicator().calculate(list(close))

    def calculate_series(self, close: Sequence[float]) -> List[Optional[float]]:
        return self._indicator().calculate_series(list(close))
