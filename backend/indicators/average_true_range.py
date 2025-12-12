"""
Average True Range wrapper.

The project historically exposed ATR via `backend/indicators/atr.py`.  This
module keeps the naming in sync with the Indicator.txt entry while reusing the
well-tested ATR implementation.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Sequence

from .atr import ATR


def _as_list(series: Sequence[float]) -> List[float]:
    return list(float(value) for value in series)


@dataclass
class AverageTrueRange:
    """Thin wrapper around :class:`backend.indicators.atr.ATR`."""

    period: int = 14

    def _indicator(self) -> ATR:
        return ATR(period=self.period)

    def calculate(self, high: Sequence[float], low: Sequence[float], close: Sequence[float]) -> Optional[float]:
        indicator = self._indicator()
        return indicator.calculate(_as_list(high), _as_list(low), _as_list(close))

    def calculate_series(
        self, high: Sequence[float], low: Sequence[float], close: Sequence[float]
    ) -> List[Optional[float]]:
        indicator = self._indicator()
        return indicator.calculate_series(_as_list(high), _as_list(low), _as_list(close))
