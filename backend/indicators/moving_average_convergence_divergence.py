"""
MACD wrapper matching Indicator.txt naming.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence

from .macd import MACD


def _to_list(values: Sequence[float]) -> List[float]:
    return list(float(v) for v in values)


@dataclass
class MovingAverageConvergenceDivergence:
    """Delegates to :class:`backend.indicators.macd.MACD`."""

    fast_period: int = 12
    slow_period: int = 26
    signal_period: int = 9

    def _indicator(self) -> MACD:
        return MACD(self.fast_period, self.slow_period, self.signal_period)

    def calculate(self, close: Sequence[float]) -> Optional[Dict[str, float]]:
        return self._indicator().calculate(_to_list(close))

    def calculate_series(self, close: Sequence[float]) -> List[Optional[Dict[str, float]]]:
        return self._indicator().calculate_series(_to_list(close))
