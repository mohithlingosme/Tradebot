"""
Volume Weighted Average Price helper wiring into :mod:`backend.indicators.vwap`.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Sequence

from .vwap import VWAP


def _as_list(values: Sequence[float]) -> List[float]:
    return list(float(v) for v in values)


@dataclass
class VolumeWeightedAveragePrice:
    """Expose VWAP using the naming from Indicator.txt."""

    def _indicator(self) -> VWAP:
        return VWAP()

    def calculate(
        self, high: Sequence[float], low: Sequence[float], close: Sequence[float], volume: Sequence[float]
    ) -> Optional[float]:
        return self._indicator().calculate(_as_list(high), _as_list(low), _as_list(close), _as_list(volume))

    def calculate_series(
        self, high: Sequence[float], low: Sequence[float], close: Sequence[float], volume: Sequence[float]
    ) -> List[Optional[float]]:
        return self._indicator().calculate_series(
            _as_list(high), _as_list(low), _as_list(close), _as_list(volume)
        )
