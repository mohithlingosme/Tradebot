"""
Shared helper functions for bespoke indicator implementations.

Many of the indicators requested in Indicator.txt build on the same moving
average, rate-of-change, or linear-regression primitives.  Keeping those
utilities in one place avoids duplicating numerical code across dozens of
modules.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Optional, Sequence, Tuple

import numpy as np


def _to_numpy(series: Sequence[float]) -> np.ndarray:
    """Convert an arbitrary numeric sequence into a 1-D numpy array."""
    arr = np.asarray(series, dtype=float)
    if arr.ndim != 1:
        raise ValueError("Indicator inputs must be one-dimensional.")
    return arr


def ensure_length(series: Sequence[float], minimum: int) -> bool:
    """Return True when the sequence has at least `minimum` samples."""
    return len(series) >= minimum


def sma(series: Sequence[float], period: int) -> Optional[float]:
    """Simple moving average of the last `period` samples."""
    if period <= 0 or not ensure_length(series, period):
        return None
    arr = _to_numpy(series)
    return float(np.mean(arr[-period:]))


def sma_series(series: Sequence[float], period: int) -> np.ndarray:
    """SMA for each point; values before `period` are NaN."""
    arr = _to_numpy(series)
    if period <= 0:
        raise ValueError("period must be positive")
    result = np.full(len(arr), np.nan, dtype=float)
    if len(arr) < period:
        return result
    window = np.convolve(arr, np.ones(period, dtype=float), "valid") / period
    result[period - 1 :] = window
    return result


def ema_series(series: Sequence[float], period: int) -> np.ndarray:
    """Exponential moving average for each sample."""
    if period <= 0:
        raise ValueError("period must be positive")
    arr = _to_numpy(series)
    if len(arr) == 0:
        return np.array([], dtype=float)
    alpha = 2.0 / (period + 1.0)
    ema = np.empty(len(arr), dtype=float)
    ema[0] = arr[0]
    for i in range(1, len(arr)):
        ema[i] = alpha * arr[i] + (1.0 - alpha) * ema[i - 1]
    return ema


def ema(series: Sequence[float], period: int) -> Optional[float]:
    """Convenience wrapper returning the latest EMA value."""
    ema_vals = ema_series(series, period)
    if ema_vals.size == 0:
        return None
    return float(ema_vals[-1])


def wma(series: Sequence[float], period: int) -> Optional[float]:
    """Weighted moving average using linear weights."""
    if period <= 0 or not ensure_length(series, period):
        return None
    arr = _to_numpy(series)[-period:]
    weights = np.arange(1, period + 1, dtype=float)
    weights /= weights.sum()
    return float(np.dot(arr, weights))


def true_range(high: Sequence[float], low: Sequence[float], close: Sequence[float]) -> np.ndarray:
    """True range vector used by ATR-style indicators."""
    high_arr, low_arr, close_arr = map(_to_numpy, (high, low, close))
    if not (len(high_arr) == len(low_arr) == len(close_arr)):
        raise ValueError("high, low, and close series must share the same length.")
    tr: np.ndarray = np.empty(len(close_arr), dtype=float)
    tr[0] = high_arr[0] - low_arr[0]
    prev_close = close_arr[0]
    for i in range(1, len(close_arr)):
        tr1 = high_arr[i] - low_arr[i]
        tr2 = abs(high_arr[i] - prev_close)
        tr3 = abs(low_arr[i] - prev_close)
        tr[i] = max(tr1, tr2, tr3)
        prev_close = close_arr[i]
    return tr


def rolling_high(series: Sequence[float], period: int) -> np.ndarray:
    """Rolling maximum."""
    arr = _to_numpy(series)
    result = np.full(len(arr), np.nan, dtype=float)
    if len(arr) < period:
        return result
    for i in range(period - 1, len(arr)):
        result[i] = float(np.max(arr[i - period + 1 : i + 1]))
    return result


def rolling_low(series: Sequence[float], period: int) -> np.ndarray:
    """Rolling minimum."""
    arr = _to_numpy(series)
    result = np.full(len(arr), np.nan, dtype=float)
    if len(arr) < period:
        return result
    for i in range(period - 1, len(arr)):
        result[i] = float(np.min(arr[i - period + 1 : i + 1]))
    return result


def rate_of_change(series: Sequence[float], period: int) -> np.ndarray:
    """Standard rate-of-change indicator expressed in percentage."""
    arr = _to_numpy(series)
    roc = np.full(len(arr), np.nan, dtype=float)
    if len(arr) <= period:
        return roc
    prev = arr[:-period]
    curr = arr[period:]
    with np.errstate(divide="ignore", invalid="ignore"):
        values = 100.0 * (curr - prev) / prev
    roc[period:] = values
    return roc


def linear_regression(series: Sequence[float], period: int) -> Tuple[np.ndarray, np.ndarray]:
    """Return regression line and slope over the rolling window."""
    arr = _to_numpy(series)
    line = np.full(len(arr), np.nan, dtype=float)
    slope = np.full(len(arr), np.nan, dtype=float)
    if len(arr) < period:
        return line, slope
    x = np.arange(period, dtype=float)
    x_mean = np.mean(x)
    denom = np.sum((x - x_mean) ** 2)
    for i in range(period - 1, len(arr)):
        window = arr[i - period + 1 : i + 1]
        y_mean = np.mean(window)
        cov = np.sum((x - x_mean) * (window - y_mean))
        m = cov / denom if denom != 0 else 0.0
        b = y_mean - m * x_mean
        slope[i] = m
        line[i] = m * (period - 1) + b
    return line, slope


def resample_by_period(values: Sequence[float], period: int) -> np.ndarray:
    """Aggregate values by taking the mean inside each period-sized bucket."""
    arr = _to_numpy(values)
    if period <= 0:
        raise ValueError("period must be positive")
    bucketed = []
    for i in range(0, len(arr), period):
        bucketed.append(np.mean(arr[i : i + period]))
    return np.asarray(bucketed, dtype=float)


@dataclass(frozen=True)
class PivotLevels:
    """Classic floor-trader pivot levels used by multiple indicators."""

    pivot: float
    resistance1: float
    resistance2: float
    support1: float
    support2: float


def pivot_levels(high: Sequence[float], low: Sequence[float], close: Sequence[float]) -> PivotLevels:
    """Compute previous-period pivot levels."""
    if not (high and low and close):
        raise ValueError("high, low, and close series must be non-empty.")
    high_arr, low_arr, close_arr = map(_to_numpy, (high, low, close))
    pivot = float((high_arr[-1] + low_arr[-1] + close_arr[-1]) / 3.0)
    range_val = float(high_arr[-1] - low_arr[-1])
    r1 = pivot + range_val
    r2 = pivot + 2 * range_val
    s1 = pivot - range_val
    s2 = pivot - 2 * range_val
    return PivotLevels(pivot=pivot, resistance1=r1, resistance2=r2, support1=s1, support2=s2)


__all__ = [
    "PivotLevels",
    "ema",
    "ema_series",
    "ensure_length",
    "linear_regression",
    "pivot_levels",
    "rate_of_change",
    "resample_by_period",
    "rolling_high",
    "rolling_low",
    "sma",
    "sma_series",
    "true_range",
    "wma",
]
