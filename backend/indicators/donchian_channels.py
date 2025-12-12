"""
Donchian Channels Indicator

Channels formed by highest high and lowest low over a period.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence

import numpy as np


@dataclass
class DonchianChannels:
    """Donchian Channels indicator."""

    period: int = 20

    def calculate(self, high: Sequence[float], low: Sequence[float]) -> Optional[Dict[str, float]]:
        """Return the Donchian Channels for the latest period."""
        if len(high) < self.period or len(low) < self.period:
            return None

        # Upper channel (highest high)
        upper = np.max(high[-self.period:])

        # Lower channel (lowest low)
        lower = np.min(low[-self.period:])

        # Middle channel (average)
        middle = (upper + lower) / 2

        return {
            'upper': float(upper),
            'middle': float(middle),
            'lower': float(lower)
        }

    def calculate_series(self, high: Sequence[float], low: Sequence[float]) -> List[Optional[Dict[str, float]]]:
        """Return Donchian Channels series."""
        if len(high) != len(low):
            return []
        channels = []
        for i in range(len(high)):
            if i < self.period - 1:
                channels.append(None)
            else:
                upper = np.max(high[i - self.period + 1 : i + 1])
                lower = np.min(low[i - self.period + 1 : i + 1])
                middle = (upper + lower) / 2
                channels.append({
                    'upper': float(upper),
                    'middle': float(middle),
                    'lower': float(lower)
                })
        return channels
