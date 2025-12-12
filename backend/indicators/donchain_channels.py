"""
Alias module for Donchian Channels.

Indicator.txt refers to the channel as "Donchain" whereas the historical
implementation in the codebase uses the `DonchianChannels` spelling.  This file
re-exports the existing logic so both spellings behave the same.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence

from .donchian_channels import DonchianChannels


def _to_list(series: Sequence[float]) -> List[float]:
    return list(float(value) for value in series)


@dataclass
class DonchainChannels:
    """Wrapper delegating to :class:`backend.indicators.donchian_channels.DonchianChannels`."""

    period: int = 20

    def _indicator(self) -> DonchianChannels:
        return DonchianChannels(period=self.period)

    def calculate(self, high: Sequence[float], low: Sequence[float]) -> Optional[Dict[str, float]]:
        return self._indicator().calculate(_to_list(high), _to_list(low))

    def calculate_series(self, high: Sequence[float], low: Sequence[float]) -> List[Optional[Dict[str, float]]]:
        return self._indicator().calculate_series(_to_list(high), _to_list(low))
