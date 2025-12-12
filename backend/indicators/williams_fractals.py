"""
Williams Fractals Indicator

Identifies reversal points using high/low patterns.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Sequence

import numpy as np


@dataclass
class WilliamsFractals:
    """Williams Fractals indicator."""

    period: int = 5

    def calculate(self, high: Sequence[float], low: Sequence[float]) -> Optional[Dict[str, bool]]:
        """Return fractal signals for the latest period."""
        if len(high) < self.period or len(low) < self.period:
            return None

        # Check for bearish fractal (high is highest in period)
        center = len(high) - self.period // 2 - 1
        if center >= 2 and center < len(high) - 2:
            bearish = high[center] == max(high[center-2:center+3])
        else:
            bearish = False

        # Check for bullish fractal (low is lowest in period)
        if center >= 2 and center < len(low) - 2:
            bullish = low[center] == min(low[center-2:center+3])
        else:
            bullish = False

        return {
            'bearish_fractal': bearish,
            'bullish_fractal': bullish
        }

    def calculate_series(self, high: Sequence[float], low: Sequence[float]) -> List[Optional[Dict[str, bool]]]:
        """Return fractal signals series."""
        if len(high) != len(low):
            return []
        fractals = []
        for i in range(len(high)):
            if i < self.period - 1:
                fractals.append(None)
            else:
                center = i - self.period // 2
                if center >= 2 and center < len(high) - 2:
                    bearish = high[center] == max(high[center-2:center+3])
                    bullish = low[center] == min(low[center-2:center+3])
                else:
                    bearish = False
                    bullish = False
                fractals.append({
                    'bearish_fractal': bearish,
                    'bullish_fractal': bullish
                })
        return fractals
