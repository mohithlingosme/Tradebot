"""
Woodies CCI implementation.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence

from .cci import CCI


@dataclass
class WoodiesCCI:
    """Return both the base CCI and the turbo CCI used in Woodies' method."""

    cci_period: int = 14
    turbo_period: int = 6

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
        base = CCI(self.cci_period)
        turbo = CCI(self.turbo_period)
        result: List[Optional[Dict[str, float]]] = []
        for idx in range(len(close)):
            base_val = base.calculate(list(high[: idx + 1]), list(low[: idx + 1]), list(close[: idx + 1]))
            turbo_val = turbo.calculate(list(high[: idx + 1]), list(low[: idx + 1]), list(close[: idx + 1]))
            if base_val is None or turbo_val is None:
                result.append(None)
            else:
                result.append({"cci": base_val, "tcci": turbo_val})
        return result
