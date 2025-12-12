"""
Relative Volume at Time (RVAT).
"""

from __future__ import annotations

from dataclasses import dataclass
from statistics import mean
from typing import List, Optional, Sequence


@dataclass
class RelativeVolumeAtTime:
    """Compare current bar's volume to the historical average for the same slot in the session."""

    session_length: int = 78

    def calculate(self, volume: Sequence[float]) -> Optional[float]:
        if len(volume) < self.session_length:
            return None
        series = self.calculate_series(volume)
        return series[-1]

    def calculate_series(self, volume: Sequence[float]) -> List[Optional[float]]:
        volumes = list(float(v) for v in volume)
        output: List[Optional[float]] = []
        for idx in range(len(volumes)):
            slot = idx % self.session_length
            historical = [volumes[i] for i in range(slot, idx, self.session_length)]
            if not historical:
                output.append(None)
                continue
            avg = mean(historical)
            output.append(volumes[idx] / avg if avg else None)
        return output
