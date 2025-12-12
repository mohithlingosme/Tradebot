"""
Wrapper around the RSI implementation.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Sequence

from .rsi import RSI


@dataclass
class RelativeStrengthIndex:
    """Expose RSI under the full indicator name."""

    period: int = 14

    def _indicator(self) -> RSI:
        return RSI(period=self.period)

    def calculate(self, close: Sequence[float]) -> Optional[float]:
        return self._indicator().calculate(list(close))

    def calculate_series(self, close: Sequence[float]) -> List[Optional[float]]:
        return self._indicator().calculate_series(list(close))
