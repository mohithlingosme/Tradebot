"""
Know Sure Thing (KST) momentum oscillator.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence

import numpy as np

from .utils import rate_of_change, sma_series


@dataclass
class KnowSureThing:
    """Implementation based on Martin Pring's specification."""

    roc1: int = 10
    roc2: int = 15
    roc3: int = 20
    roc4: int = 30
    sma1: int = 10
    sma2: int = 10
    sma3: int = 10
    sma4: int = 15
    signal_period: int = 9

    def calculate(self, close: Sequence[float]) -> Optional[Dict[str, float]]:
        values = self.calculate_series(close)
        return values[-1] if values else None

    def calculate_series(self, close: Sequence[float]) -> List[Optional[Dict[str, float]]]:
        roc1 = rate_of_change(close, self.roc1)
        roc2 = rate_of_change(close, self.roc2)
        roc3 = rate_of_change(close, self.roc3)
        roc4 = rate_of_change(close, self.roc4)

        rcma1 = sma_series(roc1, self.sma1)
        rcma2 = sma_series(roc2, self.sma2)
        rcma3 = sma_series(roc3, self.sma3)
        rcma4 = sma_series(roc4, self.sma4)

        kst_values = (
            1 * rcma1
            + 2 * rcma2
            + 3 * rcma3
            + 4 * rcma4
        )
        signal_series = sma_series(kst_values, self.signal_period)
        output: List[Optional[Dict[str, float]]] = []
        for kst, signal in zip(kst_values, signal_series):
            if np.isnan(kst):
                output.append(None)
            else:
                output.append({"kst": float(kst), "signal": float(signal) if not np.isnan(signal) else None})
        return output
