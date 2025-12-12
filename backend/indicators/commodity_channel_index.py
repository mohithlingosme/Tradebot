"""
Commodity Channel Index convenience wrapper.

The canonical implementation lives in :mod:`backend.indicators.cci`.  This
module keeps Indicator.txt aligned by exposing a class whose name matches the
text description.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Sequence

from .cci import CCI


def _to_list(series: Sequence[float]) -> List[float]:
    return list(float(value) for value in series)


@dataclass
class CommodityChannelIndex:
    """Delegates to :class:`backend.indicators.cci.CCI`."""

    period: int = 20

    def _indicator(self) -> CCI:
        return CCI(period=self.period)

    def calculate(self, high: Sequence[float], low: Sequence[float], close: Sequence[float]) -> Optional[float]:
        return self._indicator().calculate(_to_list(high), _to_list(low), _to_list(close))

    def calculate_series(
        self, high: Sequence[float], low: Sequence[float], close: Sequence[float]
    ) -> List[Optional[float]]:
        return self._indicator().calculate_series(_to_list(high), _to_list(low), _to_list(close))
