"""
Vortex indicator implementation.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence


@dataclass
class VortexIndicator:
    """Compute VI+ and VI- lines."""

    period: int = 14

    def calculate(
        self,
        high: Sequence[float],
        low: Sequence[float],
        close: Sequence[float],
    ) -> Optional[Dict[str, float]]:
        values = self.calculate_series(high, low, close)
        return values[-1] if values else None

    def calculate_series(
        self,
        high: Sequence[float],
        low: Sequence[float],
        close: Sequence[float],
    ) -> List[Optional[Dict[str, float]]]:
        if not (len(high) == len(low) == len(close)):
            return []
        vmp: List[float] = [0.0]
        vmn: List[float] = [0.0]
        tr: List[float] = [high[0] - low[0]]
        for i in range(1, len(close)):
            vmp.append(abs(high[i] - low[i - 1]))
            vmn.append(abs(low[i] - high[i - 1]))
            tr1 = high[i] - low[i]
            tr2 = abs(high[i] - close[i - 1])
            tr3 = abs(low[i] - close[i - 1])
            tr.append(max(tr1, tr2, tr3))
        output: List[Optional[Dict[str, float]]] = []
        for idx in range(len(close)):
            if idx < self.period:
                output.append(None)
                continue
            sum_tr = sum(tr[idx - self.period + 1 : idx + 1])
            sum_vmp = sum(vmp[idx - self.period + 1 : idx + 1])
            sum_vmn = sum(vmn[idx - self.period + 1 : idx + 1])
            if sum_tr == 0:
                output.append(None)
            else:
                output.append(
                    {
                        "vi_plus": sum_vmp / sum_tr,
                        "vi_minus": sum_vmn / sum_tr,
                    }
                )
        return output
