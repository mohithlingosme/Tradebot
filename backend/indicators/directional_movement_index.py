"""
Directional Movement Index built from the ADX helper.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence

from .adx import ADX


def _to_list(values: Sequence[float]) -> List[float]:
    return list(float(v) for v in values)


@dataclass
class DirectionalMovementIndex:
    """Expose +DI/-DI readings without forcing callers to parse the ADX dict."""

    period: int = 14

    def _indicator(self) -> ADX:
        return ADX(period=self.period)

    def calculate(self, high: Sequence[float], low: Sequence[float], close: Sequence[float]) -> Optional[Dict[str, float]]:
        result = self._indicator().calculate(_to_list(high), _to_list(low), _to_list(close))
        if result is None:
            return None
        return {
            "plus_di": result["plus_di"],
            "minus_di": result["minus_di"],
            "adx": result["adx"],
        }

    def calculate_series(
        self, high: Sequence[float], low: Sequence[float], close: Sequence[float]
    ) -> List[Optional[Dict[str, float]]]:
        series = self._indicator().calculate_series(_to_list(high), _to_list(low), _to_list(close))
        output: List[Optional[Dict[str, float]]] = []
        for value in series:
            if value is None:
                output.append(None)
            else:
                output.append(
                    {"plus_di": value["plus_di"], "minus_di": value["minus_di"], "adx": value["adx"]}
                )
        return output
