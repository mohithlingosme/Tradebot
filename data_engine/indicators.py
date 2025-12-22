from __future__ import annotations

"""Indicator helpers (VWAP, ATR)."""

from typing import Iterable, List, Literal, Optional, Sequence

from .candle import Candle
from .rolling import Number


def calc_vwap(prices: Sequence[Number], volumes: Sequence[Number]) -> Optional[float]:
    """
    Calculate VWAP from price/volume sequences.
    """
    if len(prices) != len(volumes):
        raise ValueError("prices and volumes must have identical length")
    total_volume = sum(float(v) for v in volumes)
    if total_volume == 0:
        return None

    weighted_sum = sum(float(p) * float(v) for p, v in zip(prices, volumes))
    return weighted_sum / total_volume


def true_range(curr_high: Number, curr_low: Number, prev_close: Optional[Number]) -> float:
    """
    True range for ATR calculations.
    """
    high_low = float(curr_high) - float(curr_low)
    if prev_close is None:
        return high_low
    high_prev = abs(float(curr_high) - float(prev_close))
    low_prev = abs(float(curr_low) - float(prev_close))
    return max(high_low, high_prev, low_prev)


def calc_atr(
    candles: Sequence[Candle],
    period: int = 14,
    method: Literal["sma", "wilder"] = "wilder",
) -> List[Optional[float]]:
    """
    Calculate ATR series aligned with the provided candles.
    """
    if period <= 1:
        raise ValueError("period must be > 1")
    tr_values = [
        true_range(candle.high, candle.low, candles[idx - 1].close if idx > 0 else None)
        for idx, candle in enumerate(candles)
    ]
    atr_values: List[Optional[float]] = []
    if method == "sma":
        for idx in range(len(tr_values)):
            if idx + 1 < period:
                atr_values.append(None)
            else:
                window = tr_values[idx - period + 1 : idx + 1]
                atr_values.append(sum(window) / period)
    elif method == "wilder":
        running_sum = 0.0
        prev_atr: Optional[float] = None
        for idx, tr in enumerate(tr_values):
            if idx < period:
                running_sum += tr
                if idx == period - 1:
                    prev_atr = running_sum / period
                    atr_values.append(prev_atr)
                else:
                    atr_values.append(None)
            else:
                assert prev_atr is not None
                atr = ((prev_atr * (period - 1)) + tr) / period
                atr_values.append(atr)
                prev_atr = atr
    else:
        raise ValueError("unsupported ATR method")
    return atr_values
