"""
SMI Ergodic indicator (aka SMI with signal line).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np

from .utils import ema_series


def _smi_series(
    high: Sequence[float],
    low: Sequence[float],
    close: Sequence[float],
    fast: int,
    slow: int,
    signal_period: int,
) -> Tuple[List[Optional[float]], List[Optional[float]]]:
    """Return (smi, signal) series."""
    if not (len(high) == len(low) == len(close)):
        return [], []
    close_arr = np.asarray(close, dtype=float)
    high_arr = np.asarray(high, dtype=float)
    low_arr = np.asarray(low, dtype=float)
    hl = high_arr - low_arr
    diff = close_arr - (high_arr + low_arr) / 2.0
    diff_ema1 = ema_series(diff, fast)
    diff_ema2 = ema_series(diff_ema1, slow)
    hl_ema1 = ema_series(hl, fast)
    hl_ema2 = ema_series(hl_ema1, slow)
    smi_raw = np.full(len(close_arr), np.nan)
    for idx in range(len(close_arr)):
        denom = 0.5 * hl_ema2[idx]
        if denom == 0:
            continue
        smi_raw[idx] = 100.0 * (diff_ema2[idx] / denom)
    signal = ema_series(smi_raw, signal_period)
    smi: List[Optional[float]] = []
    sig: List[Optional[float]] = []
    for smi_val, sig_val in zip(smi_raw, signal):
        smi.append(float(smi_val) if not np.isnan(smi_val) else None)
        sig.append(float(sig_val) if not np.isnan(sig_val) else None)
    return smi, sig


@dataclass
class SMIErgodicIndicator:
    """Return the SMI line and its moving-average signal."""

    fast: int = 5
    slow: int = 13
    signal: int = 5

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
        smi, signal = _smi_series(high, low, close, self.fast, self.slow, self.signal)
        output: List[Optional[Dict[str, float]]] = []
        for smi_val, sig_val in zip(smi, signal):
            if smi_val is None:
                output.append(None)
            else:
                output.append({"smi": smi_val, "signal": sig_val})
        return output


__all__ = ["SMIErgodicIndicator", "_smi_series"]
