"""
SMI Ergodic oscillator (difference between SMI and its signal).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Sequence

from .smi_ergodic_indicator import _smi_series


@dataclass
class SMIErgodicOscillator:
    """Return the oscillator line derived from the ergodic indicator."""

    fast: int = 5
    slow: int = 13
    signal: int = 5

    def calculate(self, high: Sequence[float], low: Sequence[float], close: Sequence[float]) -> Optional[float]:
        series = self.calculate_series(high, low, close)
        return series[-1] if series else None

    def calculate_series(self, high: Sequence[float], low: Sequence[float], close: Sequence[float]) -> List[Optional[float]]:
        smi, signal = _smi_series(high, low, close, self.fast, self.slow, self.signal)
        oscillator: List[Optional[float]] = []
        for smi_val, sig_val in zip(smi, signal):
            if smi_val is None or sig_val is None:
                oscillator.append(None)
            else:
                oscillator.append(smi_val - sig_val)
        return oscillator
