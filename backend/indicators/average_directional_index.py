"""
Average Directional Index convenience wrapper.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence

from .adx import ADX


def _to_list(values: Sequence[float]) -> List[float]:
    return list(float(v) for v in values)


@dataclass
class AverageDirectionalIndex:
    """Delegates to :class:`backend.indicators.adx.ADX`."""

    period: int = 14

    def _indicator(self) -> ADX:
        return ADX(period=self.period)

    def calculate(self, high: Sequence[float], low: Sequence[float], close: Sequence[float]) -> Optional[Dict[str, float]]:
        return self._indicator().calculate(_to_list(high), _to_list(low), _to_list(close))

    def calculate_series(
        self, high: Sequence[float], low: Sequence[float], close: Sequence[float]
    ) -> List[Optional[Dict[str, float]]]:
        return self._indicator().calculate_series(_to_list(high), _to_list(low), _to_list(close))
