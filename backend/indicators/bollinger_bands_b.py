"""
Bollinger %B helper.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Sequence

from .bollinger_bands import BollingerBands


@dataclass
class BollingerBandsPercentB:
    """Convenience class returning Bollinger %B for Indicator.txt compatibility."""

    period: int = 20
    std_dev_multiplier: float = 2.0

    def _indicator(self) -> BollingerBands:
        return BollingerBands(period=self.period, std_dev_multiplier=self.std_dev_multiplier)

    def calculate(self, close: Sequence[float]) -> Optional[float]:
        data = self._indicator().calculate(list(close))
        return data["percent_b"] if data else None

    def calculate_series(self, close: Sequence[float]) -> List[Optional[float]]:
        series = self._indicator().calculate_series(list(close))
        output: List[Optional[float]] = []
        for entry in series:
            output.append(entry["percent_b"] if entry else None)
        return output
