"""
Typo-friendly wrapper for the True Strength Index.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Sequence

from .true_strength_index import TrueStrengthIndex as _TrueStrengthIndex


def _to_list(values: Sequence[float]) -> List[float]:
    return list(float(v) for v in values)


@dataclass
class TrueStrenghtIndex:
    """Expose ``TrueStrengthIndex`` under the misspelled module/class name."""

    short_period: int = 25
    long_period: int = 13

    def _indicator(self) -> _TrueStrengthIndex:
        return _TrueStrengthIndex(short_period=self.short_period, long_period=self.long_period)

    def calculate(self, close: Sequence[float]) -> Optional[float]:
        return self._indicator().calculate(_to_list(close))

    def calculate_series(self, close: Sequence[float]) -> List[Optional[float]]:
        return self._indicator().calculate_series(_to_list(close))
