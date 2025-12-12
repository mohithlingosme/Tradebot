"""
Williams Alligator Indicator

Uses three smoothed moving averages to identify trends.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence

import numpy as np


@dataclass
class WilliamsAlligator:
    """Williams Alligator indicator."""

    jaw_period: int = 13
    teeth_period: int = 8
    lips_period: int = 5
    jaw_shift: int = 8
    teeth_shift: int = 5
    lips_shift: int = 3

    def calculate(self, high: Sequence[float], low: Sequence[float]) -> Optional[Dict[str, float]]:
        """Return the Alligator components for the latest period."""
        if len(high) < max(self.jaw_period + self.jaw_shift, self.teeth_period + self.teeth_shift, self.lips_period + self.lips_shift):
            return None

        # Calculate median prices
        median = (np.array(high) + np.array(low)) / 2

        # Jaw (Blue) - Smoothed MA with shift
        jaw = self._smma(median[-self.jaw_period - self.jaw_shift : -self.jaw_shift or None])

        # Teeth (Red) - Smoothed MA with shift
        teeth = self._smma(median[-self.teeth_period - self.teeth_shift : -self.teeth_shift or None])

        # Lips (Green) - Smoothed MA with shift
        lips = self._smma(median[-self.lips_period - self.lips_shift : -self.lips_shift or None])

        return {
            'jaw': float(jaw),
            'teeth': float(teeth),
            'lips': float(lips)
        }

    def calculate_series(self, high: Sequence[float], low: Sequence[float]) -> List[Optional[Dict[str, float]]]:
        """Return Alligator series."""
        if len(high) != len(low):
            return []
        alligator = []
        median = (np.array(high) + np.array(low)) / 2
        for i in range(len(median)):
            if i < max(self.jaw_period + self.jaw_shift, self.teeth_period + self.teeth_shift, self.lips_period + self.lips_shift) - 1:
                alligator.append(None)
            else:
                jaw = self._smma(median[i - self.jaw_period - self.jaw_shift + 1 : i - self.jaw_shift + 1])
                teeth = self._smma(median[i - self.teeth_period - self.teeth_shift + 1 : i - self.teeth_shift + 1])
                lips = self._smma(median[i - self.lips_period - self.lips_shift + 1 : i - self.lips_shift + 1])
                alligator.append({
                    'jaw': float(jaw),
                    'teeth': float(teeth),
                    'lips': float(lips)
                })
        return alligator

    def _smma(self, data: Sequence[float]) -> float:
        """Calculate Smoothed Moving Average."""
        if len(data) == 0:
            return 0.0
        smma = data[0]
        for i in range(1, len(data)):
            smma = (smma * (len(data) - 1) + data[i]) / len(data)
        return smma
