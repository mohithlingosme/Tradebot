"""
Lightweight technical indicator helpers used by strategies.
"""

from __future__ import annotations

from math import sqrt
from statistics import mean, pstdev
from typing import Dict, List, Optional, Tuple


def sma(values: List[float], period: int) -> Optional[float]:
    if len(values) < period or period <= 0:
        return None
    return float(mean(values[-period:]))


def ema(values: List[float], period: int) -> Optional[float]:
    if len(values) < period or period <= 0:
        return None

    alpha = 2 / (period + 1)
    ema_value = sma(values[:period], period)
    if ema_value is None:
        return None

    for price in values[period:]:
        ema_value = (price - ema_value) * alpha + ema_value
    return float(ema_value)


def rsi(values: List[float], period: int) -> Optional[float]:
    if len(values) <= period:
        return None

    gains = []
    losses = []
    for prev, curr in zip(values[-period - 1 : -1], values[-period:]):
        change = curr - prev
        if change >= 0:
            gains.append(change)
        else:
            losses.append(abs(change))

    avg_gain = mean(gains) if gains else 0.0
    avg_loss = mean(losses) if losses else 0.0
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))


def macd(values: List[float], fast: int = 12, slow: int = 26, signal_period: int = 9) -> Optional[Dict[str, float]]:
    if len(values) < slow + signal_period:
        return None

    fast_ema = ema(values, fast)
    slow_ema = ema(values, slow)
    if fast_ema is None or slow_ema is None:
        return None

    macd_line = fast_ema - slow_ema

    # Build signal line using recent MACD history for stability
    macd_history: List[float] = []
    for i in range(len(values) - slow, len(values)):
        window = values[: i + 1]
        fast_val = ema(window, fast)
        slow_val = ema(window, slow)
        if fast_val is not None and slow_val is not None:
            macd_history.append(fast_val - slow_val)

    signal_line = ema(macd_history, signal_period) if macd_history else None
    histogram = macd_line - signal_line if signal_line is not None else 0.0

    return {
        "macd_line": macd_line,
        "signal_line": signal_line if signal_line is not None else 0.0,
        "histogram": histogram,
    }


def bollinger_bands(values: List[float], period: int = 20, num_std: float = 2.0) -> Optional[Tuple[float, float, float]]:
    if len(values) < period:
        return None

    window = values[-period:]
    mid = sma(window, period)
    if mid is None:
        return None

    deviation = pstdev(window) if len(window) > 1 else 0.0
    upper = mid + num_std * deviation
    lower = mid - num_std * deviation
    return mid, upper, lower


def volatility(values: List[float], period: int = 20) -> Optional[float]:
    if len(values) < period:
        return None
    window = values[-period:]
    return pstdev(window) * sqrt(period)
