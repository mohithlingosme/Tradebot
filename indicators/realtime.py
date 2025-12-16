"""
Real-Time Technical Indicators Module for FINBOT

This module provides efficient, vectorized implementations of technical indicators
for real-time algorithmic trading. It uses a stateful RollingWindow for data buffering
and pure functions for indicator calculations.
"""

from collections import deque
from dataclasses import dataclass
from typing import List, Optional, Tuple, Dict, Any
import numpy as np
import pandas as pd


@dataclass
class Candle:
    """Represents a single OHLCV candle."""
    open: float
    high: float
    low: float
    close: float
    volume: float


class RollingWindow:
    """
    A fixed-size buffer for storing the last N candles using collections.deque.

    This class manages the state of historical data, allowing efficient addition
    of new candles and retrieval as numpy arrays for vectorized calculations.
    """

    def __init__(self, max_length: int):
        self.max_length = max_length
        self.buffer: deque[Candle] = deque(maxlen=max_length)

    def add_candle(self, candle: Candle) -> None:
        """Add a new candle to the rolling window."""
        self.buffer.append(candle)

    def get_closes(self) -> np.ndarray:
        """Return array of closing prices."""
        return np.array([c.close for c in self.buffer])

    def get_highs(self) -> np.ndarray:
        """Return array of high prices."""
        return np.array([c.high for c in self.buffer])

    def get_lows(self) -> np.ndarray:
        """Return array of low prices."""
        return np.array([c.low for c in self.buffer])

    def get_opens(self) -> np.ndarray:
        """Return array of opening prices."""
        return np.array([c.open for c in self.buffer])

    def get_volumes(self) -> np.ndarray:
        """Return array of volumes."""
        return np.array([c.volume for c in self.buffer])

    def is_full(self) -> bool:
        """Check if the buffer is at maximum capacity."""
        return len(self.buffer) == self.max_length

    def __len__(self) -> int:
        return len(self.buffer)


def twenty_four_hour_volume(volumes: np.ndarray) -> float:
    """
    Calculate 24-hour volume as rolling sum over last 1440 minutes (assuming 1-min bars).

    Formula: sum(volumes[-1440:])
    """
    if len(volumes) < 1440:
        return np.sum(volumes)
    return np.sum(volumes[-1440:])


def accumulation_distribution(highs: np.ndarray, lows: np.ndarray,
                             closes: np.ndarray, volumes: np.ndarray) -> np.ndarray:
    """
    Calculate Chaikin Accumulation/Distribution Line.

    Formula: A/D = cumulative sum of [(close - low) - (high - close)] / (high - low) * volume
    """
    # Avoid division by zero
    hl_diff = highs - lows
    hl_diff = np.where(hl_diff == 0, 1e-8, hl_diff)

    ad_values = ((closes - lows) - (highs - closes)) / hl_diff * volumes
    return np.cumsum(ad_values)


def advance_decline_line(advances: List[float], declines: List[float]) -> np.ndarray:
    """
    Calculate Advance-Decline Line.

    Formula: ADL = cumulative sum of (advances - declines)
    """
    adv_arr = np.array(advances)
    dec_arr = np.array(declines)
    return np.cumsum(adv_arr - dec_arr)


def advance_decline_ratio(advances: List[float], declines: List[float]) -> np.ndarray:
    """
    Calculate Advance-Decline Ratio.

    Formula: ADR = advances / declines
    """
    adv_arr = np.array(advances)
    dec_arr = np.array(declines)
    # Avoid division by zero
    dec_arr = np.where(dec_arr == 0, 1e-8, dec_arr)
    return adv_arr / dec_arr


def advance_decline_ratio_bars(opens: np.ndarray, closes: np.ndarray, n: int) -> float:
    """
    Calculate Advance/Decline Ratio (Bars) over last N bars.

    Formula: Ratio of green candles (close > open) to red candles (close < open)
    """
    if len(closes) < n or len(opens) < n:
        n = min(len(closes), len(opens))

    recent_opens = opens[-n:]
    recent_closes = closes[-n:]

    green = np.sum(recent_closes > recent_opens)
    red = np.sum(recent_closes < recent_opens)

    if red == 0:
        return float('inf') if green > 0 else 0.0
    return green / red


def alma(prices: np.ndarray, window: int, offset: float = 0.85, sigma: float = 6.0) -> np.ndarray:
    """
    Calculate Arnaud Legoux Moving Average using Gaussian filter.

    Formula: ALMA = sum(w_i * price_i) / sum(w_i)
    where w_i = exp(-((i - m*offset)^2) / (2*sigma^2))
    m = window - 1
    """
    if len(prices) < window:
        return np.array([])

    result = np.zeros(len(prices) - window + 1)

    for i in range(window, len(prices) + 1):
        data = prices[i-window:i]
        m = window - 1
        weights = np.exp(-((np.arange(window) - m * offset) ** 2) / (2 * sigma ** 2))
        weights /= np.sum(weights)
        result[i - window] = np.sum(data * weights)

    return result


def aroon(highs: np.ndarray, lows: np.ndarray, period: int) -> Tuple[np.ndarray, np.ndarray]:
    """
    Calculate Aroon Up and Aroon Down indicators.

    Formula:
    Aroon Up = ((period - days_since_highest_high) / period) * 100
    Aroon Down = ((period - days_since_lowest_low) / period) * 100
    """
    if len(highs) < period or len(lows) < period:
        return np.array([]), np.array([])

    aroon_up = np.zeros(len(highs) - period + 1)
    aroon_down = np.zeros(len(highs) - period + 1)

    for i in range(period - 1, len(highs)):
        high_window = highs[i-period+1:i+1]
        low_window = lows[i-period+1:i+1]

        days_since_high = period - 1 - np.argmax(high_window)
        days_since_low = period - 1 - np.argmin(low_window)

        aroon_up[i - period + 1] = ((period - days_since_high) / period) * 100
        aroon_down[i - period + 1] = ((period - days_since_low) / period) * 100

    return aroon_up, aroon_down


def get_pivots(highs: np.ndarray, lows: np.ndarray, length: int) -> Tuple[np.ndarray, np.ndarray]:
    """
    Identify pivot points (local maxima and minima).

    A pivot high is identified if the high is greater than the highs of the previous
    and next 'length' bars. Similarly for pivot lows.

    Returns: (pivot_highs_indices, pivot_lows_indices)
    """
    if len(highs) < 2 * length + 1:
        return np.array([]), np.array([])

    pivot_highs = []
    pivot_lows = []

    for i in range(length, len(highs) - length):
        # Check for pivot high
        is_high = all(highs[i] > highs[i-j] for j in range(1, length+1)) and \
                  all(highs[i] > highs[i+j] for j in range(1, length+1))
        if is_high:
            pivot_highs.append(i)

        # Check for pivot low
        is_low = all(lows[i] < lows[i-j] for j in range(1, length+1)) and \
                 all(lows[i] < lows[i+j] for j in range(1, length+1))
        if is_low:
            pivot_lows.append(i)

    return np.array(pivot_highs), np.array(pivot_lows)


def auto_fib_retracement(highs: np.ndarray, lows: np.ndarray, length: int = 5) -> Dict[str, float]:
    """
    Calculate Auto Fibonacci Retracement levels based on last significant high and low.

    Uses the most recent confirmed pivot high and low to determine the range.
    Levels: 0, 0.236, 0.382, 0.5, 0.618, 0.786, 1.0
    """
    pivot_highs, pivot_lows = get_pivots(highs, lows, length)

    if len(pivot_highs) == 0 or len(pivot_lows) == 0:
        return {}

    # Find the most recent high and low
    recent_high_idx = pivot_highs[-1]
    recent_low_idx = pivot_lows[-1]

    # Determine the range
    if recent_high_idx > recent_low_idx:
        # High after low: retracement from low to high
        low = lows[recent_low_idx]
        high = highs[recent_high_idx]
    else:
        # Low after high: retracement from high to low
        low = lows[recent_low_idx]
        high = highs[recent_high_idx]

    diff = high - low
    levels = {
        '0.0': low,
        '0.236': low + 0.236 * diff,
        '0.382': low + 0.382 * diff,
        '0.5': low + 0.5 * diff,
        '0.618': low + 0.618 * diff,
        '0.786': low + 0.786 * diff,
        '1.0': high
    }

    return levels


def auto_fib_extension(highs: np.ndarray, lows: np.ndarray, length: int = 5) -> Dict[str, float]:
    """
    Calculate Auto Fibonacci Extension levels based on last 3 significant pivots.

    Identifies the last 3 pivots (high-low-high or low-high-low) and calculates
    extension levels: 1.0, 1.272, 1.618
    """
    pivot_highs, pivot_lows = get_pivots(highs, lows, length)

    if len(pivot_highs) + len(pivot_lows) < 3:
        return {}

    # Get last 3 pivots, sorted by index
    all_pivots = []
    for idx in pivot_highs:
        all_pivots.append(('high', idx, highs[idx]))
    for idx in pivot_lows:
        all_pivots.append(('low', idx, lows[idx]))

    all_pivots.sort(key=lambda x: x[1])
    recent_pivots = all_pivots[-3:]

    if len(recent_pivots) < 3:
        return {}

    # Determine pattern: should be alternating high-low-high or low-high-low
    types = [p[0] for p in recent_pivots]
    if not ((types == ['high', 'low', 'high']) or (types == ['low', 'high', 'low'])):
        return {}

    # Calculate extension from the last two points
    p1 = recent_pivots[-2][2]  # Second last pivot value
    p2 = recent_pivots[-1][2]  # Last pivot value

    diff = abs(p2 - p1)
    direction = 1 if p2 > p1 else -1

    levels = {
        '1.0': p2,
        '1.272': p2 + direction * 0.272 * diff,
        '1.618': p2 + direction * 0.618 * diff
    }

    return levels


def auto_pitchfork(highs: np.ndarray, lows: np.ndarray, length: int = 5) -> Dict[str, Tuple[float, float, float]]:
    """
    Calculate Auto Pitchfork based on last 3 significant pivots.

    Identifies the last 3 pivots and calculates:
    - Median Line: between first and third pivot
    - Upper Parallel: parallel to median, touching second pivot
    - Lower Parallel: parallel to median, below/above based on direction
    """
    pivot_highs, pivot_lows = get_pivots(highs, lows, length)

    if len(pivot_highs) + len(pivot_lows) < 3:
        return {}

    # Get last 3 pivots
    all_pivots = []
    for idx in pivot_highs:
        all_pivots.append(('high', idx, highs[idx]))
    for idx in pivot_lows:
        all_pivots.append(('low', idx, lows[idx]))

    all_pivots.sort(key=lambda x: x[1])
    recent_pivots = all_pivots[-3:]

    if len(recent_pivots) < 3:
        return {}

    # Extract points
    p1 = recent_pivots[0][2]
    p2 = recent_pivots[1][2]
    p3 = recent_pivots[2][2]

    # Median line: from p1 to p3
    median_slope = (p3 - p1) / 2  # Assuming equal time intervals

    # Upper parallel: parallel to median, passing through p2
    upper_intercept = p2 - median_slope

    # Lower parallel: symmetric below median
    lower_intercept = p1 - (p2 - p1)

    # Return as (slope, intercept) tuples
    return {
        'median_line': (median_slope, p1),
        'upper_parallel': (median_slope, upper_intercept),
        'lower_parallel': (median_slope, lower_intercept)
    }


def auto_trendlines(highs: np.ndarray, lows: np.ndarray, length: int = 5) -> Dict[str, Tuple[float, float]]:
    """
    Calculate Auto Trendlines based on last significant pivots.

    Identifies the last two pivots of the same type (highs or lows) and draws a trendline.
    Returns slope and intercept for support/resistance lines.
    """
    pivot_highs, pivot_lows = get_pivots(highs, lows, length)

    if len(pivot_highs) < 2 and len(pivot_lows) < 2:
        return {}

    # Try resistance line from last two highs
    if len(pivot_highs) >= 2:
        idx1, idx2 = pivot_highs[-2], pivot_highs[-1]
        p1, p2 = highs[idx1], highs[idx2]
        slope = (p2 - p1) / (idx2 - idx1) if idx2 != idx1 else 0
        intercept = p1 - slope * idx1
        return {'resistance': (slope, intercept)}

    # Try support line from last two lows
    if len(pivot_lows) >= 2:
        idx1, idx2 = pivot_lows[-2], pivot_lows[-1]
        p1, p2 = lows[idx1], lows[idx2]
        slope = (p2 - p1) / (idx2 - idx1) if idx2 != idx1 else 0
        intercept = p1 - slope * idx1
        return {'support': (slope, intercept)}

    return {}


def average_day_range(highs: np.ndarray, lows: np.ndarray, period: int = 14) -> np.ndarray:
    """
    Calculate Average Day Range over a rolling period.

    Formula: SMA of (high - low) over 'period' days.
    """
    ranges = highs - lows
    if len(ranges) < period:
        return np.array([])
    return pd.Series(ranges).rolling(window=period).mean().values[period-1:]


def average_directional_index(highs: np.ndarray, lows: np.ndarray, closes: np.ndarray, period: int = 14) -> np.ndarray:
    """
    Calculate Average Directional Index (ADX).

    Formula: ADX = SMA of DX, where DX = 100 * |DI+ - DI-| / (DI+ + DI-)
    DI+ = 100 * SMA(+DM) / ATR, DI- = 100 * SMA(-DM) / ATR
    +DM = high - high_prev if high - high_prev > low_prev - low, else 0
    -DM = low_prev - low if low_prev - low > high - high_prev, else 0
    """
    if len(highs) < period + 1:
        return np.array([])

    # Calculate True Range
    tr = np.maximum(highs[1:] - lows[1:],
                    np.maximum(np.abs(highs[1:] - closes[:-1]), np.abs(lows[1:] - closes[:-1])))

    # Directional Movement
    dm_plus = np.where((highs[1:] - highs[:-1]) > (lows[:-1] - lows[1:]), highs[1:] - highs[:-1], 0)
    dm_minus = np.where((lows[:-1] - lows[1:]) > (highs[1:] - highs[:-1]), lows[:-1] - lows[1:], 0)

    # Smoothed averages
    atr = pd.Series(tr).rolling(window=period).mean().values
    di_plus = 100 * pd.Series(dm_plus).rolling(window=period).mean().values / atr
    di_minus = 100 * pd.Series(dm_minus).rolling(window=period).mean().values / atr

    dx = 100 * np.abs(di_plus - di_minus) / (di_plus + di_minus)
    dx = np.nan_to_num(dx, nan=0)
    adx = pd.Series(dx).rolling(window=period).mean().values[period-1:]

    return adx


def average_true_range(highs: np.ndarray, lows: np.ndarray, closes: np.ndarray, period: int = 14) -> np.ndarray:
    """
    Calculate Average True Range (ATR).

    Formula: ATR = SMA of True Range, where TR = max(high-low, |high-prev_close|, |low-prev_close|)
    """
    if len(highs) < 2:
        return np.array([])

    tr = np.maximum(highs[1:] - lows[1:],
                    np.maximum(np.abs(highs[1:] - closes[:-1]), np.abs(lows[1:] - closes[:-1])))
    return pd.Series(tr).rolling(window=period).mean().values[period-1:]


def awesome_oscillator(highs: np.ndarray, lows: np.ndarray, short_period: int = 5, long_period: int = 34) -> np.ndarray:
    """
    Calculate Awesome Oscillator.

    Formula: AO = SMA(median_price, short) - SMA(median_price, long)
    where median_price = (high + low) / 2
    """
    median_price = (highs + lows) / 2
    short_sma = pd.Series(median_price).rolling(window=short_period).mean()
    long_sma = pd.Series(median_price).rolling(window=long_period).mean()
    ao = short_sma - long_sma
    return ao.values[long_period-1:]


def balance_of_power(opens: np.ndarray, highs: np.ndarray, lows: np.ndarray, closes: np.ndarray) -> np.ndarray:
    """
    Calculate Balance of Power.

    Formula: BOP = (close - open) / (high - low)
    """
    hl_diff = highs - lows
    hl_diff = np.where(hl_diff == 0, 1e-8, hl_diff)
    return (closes - opens) / hl_diff


def bbtrend(closes: np.ndarray, period: int = 20, std_dev: float = 2.0) -> np.ndarray:
    """
    Calculate BBTrend (Bollinger Band Trend).

    Formula: Trend based on position relative to bands. 1 if above upper, -1 if below lower, 0 otherwise.
    """
    if len(closes) < period:
        return np.array([])

    sma = pd.Series(closes).rolling(window=period).mean()
    std = pd.Series(closes).rolling(window=period).std()
    upper = sma + std_dev * std
    lower = sma - std_dev * std

    trend = np.zeros(len(closes))
    trend[closes > upper] = 1
    trend[closes < lower] = -1
    return trend[period-1:]


def bollinger_bands(closes: np.ndarray, period: int = 20, std_dev: float = 2.0) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Calculate Bollinger Bands.

    Formula: Middle = SMA(close), Upper = Middle + std_dev * Std, Lower = Middle - std_dev * Std
    """
    if len(closes) < period:
        return np.array([]), np.array([]), np.array([])

    sma = pd.Series(closes).rolling(window=period).mean()
    std = pd.Series(closes).rolling(window=period).std()
    upper = sma + std_dev * std
    lower = sma - std_dev * std
    return upper.values, sma.values, lower.values


def bollinger_bands_percent_b(closes: np.ndarray, period: int = 20, std_dev: float = 2.0) -> np.ndarray:
    """
    Calculate Bollinger Bands %B.

    Formula: %B = (close - Lower) / (Upper - Lower)
    """
    upper, middle, lower = bollinger_bands(closes, period, std_dev)
    if len(upper) == 0:
        return np.array([])
    band_width = upper - lower
    band_width = np.where(band_width == 0, 1e-8, band_width)
    return (closes[period-1:] - lower) / band_width


def bollinger_bandwidth(closes: np.ndarray, period: int = 20, std_dev: float = 2.0) -> np.ndarray:
    """
    Calculate Bollinger Bandwidth.

    Formula: Bandwidth = (Upper - Lower) / Middle
    """
    upper, middle, lower = bollinger_bands(closes, period, std_dev)
    if len(upper) == 0:
        return np.array([])
    return (upper - lower) / middle


def bollinger_bars(closes: np.ndarray, period: int = 20, std_dev: float = 2.0) -> np.ndarray:
    """
    Calculate Bollinger Bars (bars since last band touch).

    Formula: Count bars since close was outside bands.
    """
    upper, middle, lower = bollinger_bands(closes, period, std_dev)
    if len(upper) == 0:
        return np.array([])

    bars = np.zeros(len(closes) - period + 1)
    last_touch = 0
    for i in range(period - 1, len(closes)):
        if closes[i] > upper[i - period + 1] or closes[i] < lower[i - period + 1]:
            last_touch = i - period + 1
        bars[i - period + 1] = i - period + 1 - last_touch
    return bars


def bull_bear_power(highs: np.ndarray, lows: np.ndarray, closes: np.ndarray, period: int = 13) -> np.ndarray:
    """
    Calculate Bull Bear Power (Elder Ray Index).

    Formula: Bull Power = high - EMA(close), Bear Power = low - EMA(close)
    Returns Bull Power (positive when bullish).
    """
    ema = pd.Series(closes).ewm(span=period).mean()
    return highs - ema.values


def chaikin_money_flow(highs: np.ndarray, lows: np.ndarray, closes: np.ndarray, volumes: np.ndarray, period: int = 21) -> np.ndarray:
    """
    Calculate Chaikin Money Flow.

    Formula: CMF = sum(AD) / sum(volume) over period, where AD = [(close-low)-(high-close)]/(high-low) * volume
    """
    if len(highs) < period:
        return np.array([])

    hl_diff = highs - lows
    hl_diff = np.where(hl_diff == 0, 1e-8, hl_diff)
    ad = ((closes - lows) - (highs - closes)) / hl_diff * volumes
    cmf = pd.Series(ad).rolling(window=period).sum() / pd.Series(volumes).rolling(window=period).sum()
    return cmf.values[period-1:]


def chaikin_oscillator(highs: np.ndarray, lows: np.ndarray, closes: np.ndarray, volumes: np.ndarray, short_period: int = 3, long_period: int = 10) -> np.ndarray:
    """
    Calculate Chaikin Oscillator.

    Formula: CO = EMA(AD, short) - EMA(AD, long), where AD is Accumulation/Distribution
    """
    ad = accumulation_distribution(highs, lows, closes, volumes)
    short_ema = pd.Series(ad).ewm(span=short_period).mean()
    long_ema = pd.Series(ad).ewm(span=long_period).mean()
    return (short_ema - long_ema).values[long_period-1:]


def know_sure_thing(closes: np.ndarray, r1: int = 10, r2: int = 15, r3: int = 20, r4: int = 30, s1: int = 10, s2: int = 10, s3: int = 10, s4: int = 15) -> np.ndarray:
    """
    Calculate Know Sure Thing (KST).

    Formula: KST = SMA(s1, ROC(r1)*1) + SMA(s2, ROC(r2)*2) + SMA(s3, ROC(r3)*3) + SMA(s4, ROC(r4)*4)
    """
    if len(closes) < r4 + s4:
        return np.array([])

    roc1 = pd.Series(closes).pct_change(r1) * 100
    roc2 = pd.Series(closes).pct_change(r2) * 100
    roc3 = pd.Series(closes).pct_change(r3) * 100
    roc4 = pd.Series(closes).pct_change(r4) * 100

    kst1 = roc1.rolling(window=s1).mean()
    kst2 = (roc2 * 2).rolling(window=s2).mean()
    kst3 = (roc3 * 3).rolling(window=s3).mean()
    kst4 = (roc4 * 4).rolling(window=s4).mean()

    kst = kst1 + kst2 + kst3 + kst4
    return kst.values[s4-1:]


def least_squares_moving_average(closes: np.ndarray, period: int) -> np.ndarray:
    """
    Calculate Least Squares Moving Average (LSMA).

    Formula: Linear regression line over the period.
    """
    if len(closes) < period:
        return np.array([])

    result = np.zeros(len(closes) - period + 1)
    x = np.arange(period)

    for i in range(period, len(closes) + 1):
        y = closes[i-period:i]
        slope, intercept = np.polyfit(x, y, 1)
        result[i - period] = intercept + slope * (period - 1)

    return result


def linear_regression_channel(closes: np.ndarray, period: int, std_dev: float = 2.0) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Calculate Linear Regression Channel.

    Formula: Regression line ± std_dev * std of residuals.
    Returns: (upper, middle, lower)
    """
    if len(closes) < period:
        return np.array([]), np.array([]), np.array([])

    result_upper = np.zeros(len(closes) - period + 1)
    result_middle = np.zeros(len(closes) - period + 1)
    result_lower = np.zeros(len(closes) - period + 1)
    x = np.arange(period)

    for i in range(period, len(closes) + 1):
        y = closes[i-period:i]
        slope, intercept = np.polyfit(x, y, 1)
        regression_line = intercept + slope * x
        residuals = y - regression_line
        std = np.std(residuals)
        middle = intercept + slope * (period - 1)
        result_middle[i - period] = middle
        result_upper[i - period] = middle + std_dev * std
        result_lower[i - period] = middle - std_dev * std

    return result_upper, result_middle, result_lower


def ma_cross(closes: np.ndarray, fast_period: int, slow_period: int) -> np.ndarray:
    """
    Calculate MA Cross signals.

    Formula: 1 if fast MA > slow MA, -1 if fast MA < slow MA, 0 otherwise.
    """
    if len(closes) < slow_period:
        return np.array([])

    fast_ma = pd.Series(closes).rolling(window=fast_period).mean()
    slow_ma = pd.Series(closes).rolling(window=slow_period).mean()
    cross = np.sign(fast_ma - slow_ma)
    return cross.values[slow_period-1:]


def mass_index(highs: np.ndarray, lows: np.ndarray, ema_period: int = 9, sum_period: int = 25) -> np.ndarray:
    """
    Calculate Mass Index.

    Formula: Sum of EMA(ema_period, high-low) / EMA(ema_period, EMA(ema_period, high-low)) over sum_period.
    """
    if len(highs) < ema_period + sum_period:
        return np.array([])

    hl = highs - lows
    ema1 = pd.Series(hl).ewm(span=ema_period).mean()
    ema2 = ema1.ewm(span=ema_period).mean()
    ratio = ema1 / ema2
    mass = ratio.rolling(window=sum_period).sum()
    return mass.values[ema_period + sum_period - 2:]


def mcginley_dynamic(closes: np.ndarray, period: int) -> np.ndarray:
    """
    Calculate McGinley Dynamic.

    Formula: MD[0] = close[0], MD[i] = MD[i-1] + (close[i] - MD[i-1]) / (0.6 * period)
    """
    if len(closes) < 1:
        return np.array([])

    md = np.zeros(len(closes))
    md[0] = closes[0]
    for i in range(1, len(closes)):
        md[i] = md[i-1] + (closes[i] - md[i-1]) / (0.6 * period)
    return md


def median(closes: np.ndarray, period: int) -> np.ndarray:
    """
    Calculate Median over period.

    Formula: Median of closes over rolling window.
    """
    if len(closes) < period:
        return np.array([])
    return pd.Series(closes).rolling(window=period).median().values[period-1:]


def momentum(closes: np.ndarray, period: int) -> np.ndarray:
    """
    Calculate Momentum.

    Formula: close - close[period]
    """
    if len(closes) < period + 1:
        return np.array([])
    return closes[period:] - closes[:-period]


def money_flow_index(highs: np.ndarray, lows: np.ndarray, closes: np.ndarray, volumes: np.ndarray, period: int = 14) -> np.ndarray:
    """
    Calculate Money Flow Index (MFI).

    Formula: RSI of money flow volume.
    """
    if len(highs) < period + 1:
        return np.array([])

    typical_price = (highs + lows + closes) / 3
    money_flow = typical_price * volumes

    positive_flow = np.where(typical_price[1:] > typical_price[:-1], money_flow[1:], 0)
    negative_flow = np.where(typical_price[1:] < typical_price[:-1], money_flow[1:], 0)

    pos_mf = pd.Series(positive_flow).rolling(window=period).sum()
    neg_mf = pd.Series(negative_flow).rolling(window=period).sum()

    mfr = pos_mf / neg_mf
    mfi = 100 - (100 / (1 + mfr))
    return mfi.values[period-1:]


def moon_phases(dates: List[str]) -> np.ndarray:
    """
    Calculate Moon Phases (simplified: 0=new, 0.5=full, etc.).

    Formula: Simplified calculation based on date. Requires dates as strings.
    """
    # This is a placeholder; real implementation would use astronomical library
    phases = []
    for date_str in dates:
        # Dummy calculation
        phase = 0.0  # Placeholder
        phases.append(phase)
    return np.array(phases)


def moving_average_convergence_divergence(closes: np.ndarray, fast_period: int = 12, slow_period: int = 26, signal_period: int = 9) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Calculate MACD.

    Formula: MACD = EMA(fast) - EMA(slow), Signal = EMA(MACD), Histogram = MACD - Signal
    Returns: (macd, signal, histogram)
    """
    if len(closes) < slow_period + signal_period:
        return np.array([]), np.array([]), np.array([])

    fast_ema = pd.Series(closes).ewm(span=fast_period).mean()
    slow_ema = pd.Series(closes).ewm(span=slow_period).mean()
    macd = fast_ema - slow_ema
    signal = macd.ewm(span=signal_period).mean()
    histogram = macd - signal
    return macd.values[slow_period-1:], signal.values[slow_period + signal_period - 2:], histogram.values[slow_period + signal_period - 2:]


def moving_average_exponential(closes: np.ndarray, period: int) -> np.ndarray:
    """
    Calculate Exponential Moving Average (EMA).

    Formula: EMA = (close * multiplier) + (prev_EMA * (1 - multiplier)), multiplier = 2 / (period + 1)
    """
    if len(closes) < period:
        return np.array([])
    return pd.Series(closes).ewm(span=period).mean().values[period-1:]


def moving_average_simple(closes: np.ndarray, period: int) -> np.ndarray:
    """
    Calculate Simple Moving Average (SMA).

    Formula: SMA = sum(closes[-period:]) / period
    """
    if len(closes) < period:
        return np.array([])
    return pd.Series(closes).rolling(window=period).mean().values[period-1:]


def moving_average_weighted(closes: np.ndarray, period: int) -> np.ndarray:
    """
    Calculate Weighted Moving Average (WMA).

    Formula: WMA = sum(weight_i * close_i) / sum(weights), weights = 1 to period
    """
    if len(closes) < period:
        return np.array([])

    weights = np.arange(1, period + 1)
    result = np.zeros(len(closes) - period + 1)

    for i in range(period, len(closes) + 1):
        data = closes[i-period:i]
        result[i - period] = np.sum(data * weights) / np.sum(weights)

    return result


def moving_average_ribbon(closes: np.ndarray, periods: List[int]) -> Dict[int, np.ndarray]:
    """
    Calculate Moving Average Ribbon (multiple SMAs).

    Formula: Dict of SMAs for each period.
    """
    ribbon = {}
    for period in periods:
        ribbon[period] = moving_average_simple(closes, period)
    return ribbon


def net_volume(volumes: np.ndarray, closes: np.ndarray, opens: np.ndarray) -> np.ndarray:
    """
    Calculate Net Volume.

    Formula: Net Volume = sum(volume * sign(close - open))
    """
    signs = np.sign(closes - opens)
    return np.cumsum(volumes * signs)


def on_balance_volume(closes: np.ndarray, volumes: np.ndarray) -> np.ndarray:
    """
    Calculate On Balance Volume (OBV).

    Formula: OBV = prev_OBV + volume if close > prev_close, prev_OBV - volume if close < prev_close
    """
    if len(closes) < 2:
        return np.array([])

    obv = np.zeros(len(closes))
    obv[0] = volumes[0]

    for i in range(1, len(closes)):
        if closes[i] > closes[i-1]:
            obv[i] = obv[i-1] + volumes[i]
        elif closes[i] < closes[i-1]:
            obv[i] = obv[i-1] - volumes[i]
        else:
            obv[i] = obv[i-1]

    return obv


def parabolic_sar(highs: np.ndarray, lows: np.ndarray, acceleration: float = 0.02, max_acceleration: float = 0.2) -> np.ndarray:
    """
    Calculate Parabolic SAR.

    Formula: SAR = prev_SAR + acceleration * (EP - prev_SAR), EP = highest high or lowest low
    """
    if len(highs) < 2:
        return np.array([])

    sar = np.zeros(len(highs))
    sar[0] = lows[0]  # Initial SAR
    ep = highs[0]  # Extreme Point
    af = acceleration  # Acceleration Factor
    uptrend = True

    for i in range(1, len(highs)):
        sar[i] = sar[i-1] + af * (ep - sar[i-1])

        if uptrend:
            if lows[i] <= sar[i]:
                uptrend = False
                sar[i] = ep
                ep = lows[i]
                af = acceleration
            else:
                if highs[i] > ep:
                    ep = highs[i]
                    af = min(af + acceleration, max_acceleration)
        else:
            if highs[i] >= sar[i]:
                uptrend = True
                sar[i] = ep
                ep = highs[i]
                af = acceleration
            else:
                if lows[i] < ep:
                    ep = lows[i]
                    af = min(af + acceleration, max_acceleration)

    return sar


def performance(closes: np.ndarray) -> np.ndarray:
    """
    Calculate Performance (cumulative return).

    Formula: (close - initial_close) / initial_close * 100
    """
    if len(closes) == 0:
        return np.array([])
    initial = closes[0]
    return (closes - initial) / initial * 100


def pivot_points_high_low(highs: np.ndarray, lows: np.ndarray, closes: np.ndarray) -> Tuple[float, float, float, float, float]:
    """
    Calculate Pivot Points (High-Low method).

    Formula: Pivot = (H + L + C) / 3, R1 = 2*P - L, S1 = 2*P - H, etc.
    Returns: (pivot, r1, s1, r2, s2)
    """
    if len(highs) == 0:
        return 0, 0, 0, 0, 0

    h = highs[-1]
    l = lows[-1]
    c = closes[-1]

    p = (h + l + c) / 3
    r1 = 2 * p - l
    s1 = 2 * p - h
    r2 = p + (h - l)
    s2 = p - (h - l)

    return p, r1, s1, r2, s2


def pivot_points_standard(highs: np.ndarray, lows: np.ndarray, closes: np.ndarray) -> Tuple[float, float, float, float, float]:
    """
    Calculate Pivot Points (Standard method).

    Formula: Same as High-Low.
    """
    return pivot_points_high_low(highs, lows, closes)


def price_oscillator(closes: np.ndarray, fast_period: int = 12, slow_period: int = 26) -> np.ndarray:
    """
    Calculate Price Oscillator.

    Formula: ((EMA(fast) - EMA(slow)) / EMA(slow)) * 100
    """
    if len(closes) < slow_period:
        return np.array([])

    fast_ema = pd.Series(closes).ewm(span=fast_period).mean()
    slow_ema = pd.Series(closes).ewm(span=slow_period).mean()
    osc = ((fast_ema - slow_ema) / slow_ema) * 100
    return osc.values[slow_period-1:]


def price_volume_trend(closes: np.ndarray, volumes: np.ndarray) -> np.ndarray:
    """
    Calculate Price Volume Trend (PVT).

    Formula: PVT = prev_PVT + volume * (close - prev_close) / prev_close
    """
    if len(closes) < 2:
        return np.array([])

    pvt = np.zeros(len(closes))
    pvt[0] = 0

    for i in range(1, len(closes)):
        change = (closes[i] - closes[i-1]) / closes[i-1]
        pvt[i] = pvt[i-1] + volumes[i] * change

    return pvt


def rate_of_change(closes: np.ndarray, period: int) -> np.ndarray:
    """
    Calculate Rate of Change (ROC).

    Formula: (close - close[period]) / close[period] * 100
    """
    if len(closes) < period + 1:
        return np.array([])
    return ((closes[period:] - closes[:-period]) / closes[:-period]) * 100


def relative_strength_index(closes: np.ndarray, period: int = 14) -> np.ndarray:
    """
    Calculate Relative Strength Index (RSI).

    Formula: RSI = 100 - (100 / (1 + RS)), RS = Average Gain / Average Loss
    """
    if len(closes) < period + 1:
        return np.array([])

    gains = np.where(closes[1:] > closes[:-1], closes[1:] - closes[:-1], 0)
    losses = np.where(closes[1:] < closes[:-1], closes[:-1] - closes[1:], 0)

    avg_gain = pd.Series(gains).rolling(window=period).mean()
    avg_loss = pd.Series(losses).rolling(window=period).mean()

    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi.values[period-1:]


def stochastic_oscillator(highs: np.ndarray, lows: np.ndarray, closes: np.ndarray, k_period: int = 14, d_period: int = 3) -> Tuple[np.ndarray, np.ndarray]:
    """
    Calculate Stochastic Oscillator.

    Formula: %K = 100 * ((C - L14) / (H14 - L14)), %D = SMA(%K, d_period)
    Returns: (%K, %D)
    """
    if len(highs) < k_period:
        return np.array([]), np.array([])

    lowest_low = pd.Series(lows).rolling(window=k_period).min()
    highest_high = pd.Series(highs).rolling(window=k_period).max()

    k = 100 * ((closes - lowest_low) / (highest_high - lowest_low))
    d = k.rolling(window=d_period).mean()
    return k.values[k_period-1:], d.values[k_period + d_period - 2:]


def supertrend(highs: np.ndarray, lows: np.ndarray, closes: np.ndarray, period: int = 7, multiplier: float = 3.0) -> Tuple[np.ndarray, np.ndarray]:
    """
    Calculate Supertrend.

    Formula: ATR-based bands with trend logic.
    Returns: (upper_band, lower_band)
    """
    atr = average_true_range(highs, lows, closes, period)
    if len(atr) == 0:
        return np.array([]), np.array([])

    hl2 = (highs + lows) / 2
    upperband = hl2 + (multiplier * atr)
    lowerband = hl2 - (multiplier * atr)

    trend = np.zeros(len(closes))
    trend[0] = 1  # assume uptrend

    for i in range(1, len(closes)):
        if closes[i] > upperband[i-1]:
            trend[i] = 1
        elif closes[i] < lowerband[i-1]:
            trend[i] = -1
        else:
            trend[i] = trend[i-1]

    final_upper = np.where(trend == 1, lowerband, upperband)
    final_lower = np.where(trend == -1, upperband, lowerband)
    return final_upper[period-1:], final_lower[period-1:]


def trix(closes: np.ndarray, period: int = 15) -> np.ndarray:
    """
    Calculate TRIX.

    Formula: Rate of change of triple EMA.
    """
    if len(closes) < period * 3:
        return np.array([])

    ema1 = pd.Series(closes).ewm(span=period).mean()
    ema2 = ema1.ewm(span=period).mean()
    ema3 = ema2.ewm(span=period).mean()
    trix = (ema3 - ema3.shift(1)) / ema3.shift(1) * 100
    return trix.values[period*3 - 2:]


def ultimate_oscillator(highs: np.ndarray, lows: np.ndarray, closes: np.ndarray, short_period: int = 7, medium_period: int = 14, long_period: int = 28) -> np.ndarray:
    """
    Calculate Ultimate Oscillator.

    Formula: Weighted average of BP/TR over different periods.
    """
    if len(highs) < long_period:
        return np.array([])

    bp = closes - np.minimum(lows, pd.Series(closes).shift(1))
    tr = np.maximum(highs - lows, np.maximum(np.abs(highs - pd.Series(closes).shift(1)), np.abs(lows - pd.Series(closes).shift(1))))

    avg7 = pd.Series(bp).rolling(window=short_period).sum() / pd.Series(tr).rolling(window=short_period).sum()
    avg14 = pd.Series(bp).rolling(window=medium_period).sum() / pd.Series(tr).rolling(window=medium_period).sum()
    avg28 = pd.Series(bp).rolling(window=long_period).sum() / pd.Series(tr).rolling(window=long_period).sum()

    uo = 100 * (4 * avg7 + 2 * avg14 + avg28) / 7
    return uo.values[long_period-1:]


def volume(volumes: np.ndarray) -> np.ndarray:
    """
    Return Volume.

    Formula: Volume itself.
    """
    return volumes


def volume_delta(volumes: np.ndarray) -> np.ndarray:
    """
    Calculate Volume Delta.

    Formula: Current volume - previous volume.
    """
    if len(volumes) < 2:
        return np.array([])
    return volumes[1:] - volumes[:-1]


def volume_oscillator(volumes: np.ndarray, short_period: int = 12, long_period: int = 26) -> np.ndarray:
    """
    Calculate Volume Oscillator.

    Formula: ((Short MA - Long MA) / Long MA) * 100
    """
    if len(volumes) < long_period:
        return np.array([])

    short_ma = pd.Series(volumes).rolling(window=short_period).mean()
    long_ma = pd.Series(volumes).rolling(window=long_period).mean()
    vo = ((short_ma - long_ma) / long_ma) * 100
    return vo.values[long_period-1:]


def volume_weighted_average_price(highs: np.ndarray, lows: np.ndarray, closes: np.ndarray, volumes: np.ndarray) -> np.ndarray:
    """
    Calculate Volume Weighted Average Price (VWAP).

    Formula: Cumulative (Typical Price * Volume) / Cumulative Volume
    """
    typical_price = (highs + lows + closes) / 3
    vwap = np.cumsum(typical_price * volumes) / np.cumsum(volumes)
    return vwap


def vortex_indicator(highs: np.ndarray, lows: np.ndarray, closes: np.ndarray, period: int = 14) -> Tuple[np.ndarray, np.ndarray]:
    """
    Calculate Vortex Indicator.

    Formula: VI+ = Sum(|H - L_prev|) / TR, VI- = Sum(|L - H_prev|) / TR
    Returns: (VI+, VI-)
    """
    if len(highs) < period + 1:
        return np.array([]), np.array([])

    vm_plus = np.abs(highs[1:] - lows[:-1])
    vm_minus = np.abs(lows[1:] - highs[:-1])
    tr = np.maximum(highs[1:] - lows[1:], np.maximum(np.abs(highs[1:] - closes[:-1]), np.abs(lows[1:] - closes[:-1])))

    vi_plus = pd.Series(vm_plus / tr).rolling(window=period).sum()
    vi_minus = pd.Series(vm_minus / tr).rolling(window=period).sum()
    return vi_plus.values[period-1:], vi_minus.values[period-1:]


def commodity_channel_index(highs: np.ndarray, lows: np.ndarray, closes: np.ndarray, period: int = 20) -> np.ndarray:
    """
    Calculate Commodity Channel Index (CCI).

    Formula: CCI = (Typical Price - SMA(Typical Price)) / (0.015 * Mean Deviation)
    where Typical Price = (High + Low + Close) / 3
    """
    if len(highs) < period:
        return np.array([])

    typical_price = (highs + lows + closes) / 3
    sma_tp = pd.Series(typical_price).rolling(window=period).mean()
    mad = pd.Series(typical_price).rolling(window=period).apply(lambda x: np.mean(np.abs(x - x.mean())), raw=False)
    cci = (typical_price - sma_tp) / (0.015 * mad)
    return cci.values[period-1:]


def vwap_auto_anchored(highs: np.ndarray, lows: np.ndarray, closes: np.ndarray, volumes: np.ndarray, anchor_index: int = 0) -> np.ndarray:
    """
    Calculate VWAP Auto Anchored from a specific anchor point.

    Formula: VWAP = Cumulative(Typical Price * Volume) / Cumulative(Volume) from anchor_index
    """
    if anchor_index >= len(highs) or len(highs) <= anchor_index:
        return np.array([])

    typical_price = (highs + lows + closes) / 3
    anchored_tp = typical_price[anchor_index:]
    anchored_vol = volumes[anchor_index:]
    vwap = np.cumsum(anchored_tp * anchored_vol) / np.cumsum(anchored_vol)
    # Pad with NaN for indices before anchor
    result = np.full(len(highs), np.nan)
    result[anchor_index:] = vwap
    return result


def williams_alligator(highs: np.ndarray, lows: np.ndarray, closes: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Calculate Williams Alligator.

    Formula: Three SMAs with shifts:
    - Jaw: SMA(13) shifted 8 bars forward
    - Teeth: SMA(8) shifted 5 bars forward
    - Lips: SMA(5) shifted 3 bars forward
    Returns: (jaw, teeth, lips)
    """
    if len(closes) < 13:
        return np.array([]), np.array([]), np.array([])

    jaw = pd.Series(closes).rolling(window=13).mean()
    teeth = pd.Series(closes).rolling(window=8).mean()
    lips = pd.Series(closes).rolling(window=5).mean()

    # Shift forward (for historical data, shift right)
    jaw_shifted = jaw.shift(8)
    teeth_shifted = teeth.shift(5)
    lips_shifted = lips.shift(3)

    return jaw_shifted.values, teeth_shifted.values, lips_shifted.values


def williams_fractals(highs: np.ndarray, lows: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """
    Calculate Williams Fractals.

    Identifies pivot points: High Fractal if high > highs of previous 2 and next 2 bars.
    Low Fractal if low < lows of previous 2 and next 2 bars.
    Returns: (fractal_highs, fractal_lows) as boolean arrays
    """
    if len(highs) < 5:
        return np.array([]), np.array([])

    fractal_highs = np.zeros(len(highs), dtype=bool)
    fractal_lows = np.zeros(len(highs), dtype=bool)

    for i in range(2, len(highs) - 2):
        if highs[i] > highs[i-2] and highs[i] > highs[i-1] and highs[i] > highs[i+1] and highs[i] > highs[i+2]:
            fractal_highs[i] = True
        if lows[i] < lows[i-2] and lows[i] < lows[i-1] and lows[i] < lows[i+1] and lows[i] < lows[i+2]:
            fractal_lows[i] = True

    return fractal_highs, fractal_lows


def woodies_cci(highs: np.ndarray, lows: np.ndarray, closes: np.ndarray, cci_period: int = 14, smooth_period: int = 2) -> np.ndarray:
    """
    Calculate Woodies CCI (Smoothed Commodity Channel Index).

    Formula: EMA(2) of CCI(14)
    """
    cci = commodity_channel_index(highs, lows, closes, cci_period)
    if len(cci) < smooth_period:
        return np.array([])
    smoothed_cci = pd.Series(cci).ewm(span=smooth_period).mean()
    return smoothed_cci.values[smooth_period-1:]


# Helper Functions
def calc_smma(prices: np.ndarray, period: int) -> np.ndarray:
    """
    Calculate Smoothed Moving Average (SMMA).

    Formula: SMMA = (SMMA_prev * (period - 1) + price) / period
    """
    if len(prices) < period:
        return np.array([])
    smma = np.zeros(len(prices))
    smma[period-1] = np.mean(prices[:period])
    for i in range(period, len(prices)):
        smma[i] = (smma[i-1] * (period - 1) + prices[i]) / period
    return smma[period-1:]


def calc_rsi_series(closes: np.ndarray, period: int = 14) -> np.ndarray:
    """
    Calculate RSI series for use in other indicators.
    """
    return relative_strength_index(closes, period)


# Batch 2 Advanced Indicators
def zig_zag(highs: np.ndarray, lows: np.ndarray, threshold: float = 0.05) -> List[Tuple[float, int]]:
    """
    Calculate Zig Zag indicator.

    Returns list of (price, index) pivots that filter out movements smaller than threshold.
    """
    if len(highs) < 3:
        return []
    pivots = []
    direction = 0  # 0: none, 1: up, -1: down
    last_pivot_price = (highs[0] + lows[0]) / 2
    last_index = 0
    for i in range(1, len(highs)):
        current_price = (highs[i] + lows[i]) / 2
        if direction == 0:
            if current_price > last_pivot_price * (1 + threshold):
                direction = 1
                last_pivot_price = current_price
                last_index = i
            elif current_price < last_pivot_price * (1 - threshold):
                direction = -1
                last_pivot_price = current_price
                last_index = i
        elif direction == 1:
            if current_price > last_pivot_price:
                last_pivot_price = current_price
                last_index = i
            elif current_price < last_pivot_price * (1 - threshold):
                pivots.append((last_pivot_price, last_index))
                direction = -1
                last_pivot_price = current_price
                last_index = i
        elif direction == -1:
            if current_price < last_pivot_price:
                last_pivot_price = current_price
                last_index = i
            elif current_price > last_pivot_price * (1 + threshold):
                pivots.append((last_pivot_price, last_index))
                direction = 1
                last_pivot_price = current_price
                last_index = i
    if last_index != len(highs) - 1:
        pivots.append((last_pivot_price, last_index))
    return pivots


def true_strength_index(closes: np.ndarray, short_period: int = 25, long_period: int = 13) -> np.ndarray:
    """
    Calculate True Strength Index (TSI).

    Formula: 100 * (DoubleSmoothed(PC) / DoubleSmoothed(AbsPC))
    """
    if len(closes) < long_period + short_period:
        return np.array([])
    pc = np.diff(closes)
    abs_pc = np.abs(pc)
    ema1_pc = pd.Series(pc).ewm(span=long_period).mean()
    ema2_pc = ema1_pc.ewm(span=short_period).mean()
    ema1_abs = pd.Series(abs_pc).ewm(span=long_period).mean()
    ema2_abs = ema1_abs.ewm(span=short_period).mean()
    tsi = 100 * (ema2_pc / ema2_abs)
    return tsi.values[long_period + short_period - 2:]


def up_down_volume(volumes: np.ndarray, closes: np.ndarray, opens: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """
    Calculate Up/Down Volume.

    Returns cumulative (up_vol, down_vol) over the rolling window.
    """
    up_vol = np.where(closes > opens, volumes, 0)
    down_vol = np.where(closes < opens, volumes, 0)
    return np.cumsum(up_vol), np.cumsum(down_vol)


def visible_average_price(highs: np.ndarray, lows: np.ndarray, closes: np.ndarray) -> float:
    """
    Calculate Visible Average Price.

    Average of all bars currently in the RollingWindow.
    """
    typical = (highs + lows + closes) / 3
    return np.mean(typical)


def volume_weighted_moving_average(closes: np.ndarray, volumes: np.ndarray, period: int) -> np.ndarray:
    """
    Calculate Volume Weighted Moving Average (VWMA).

    Formula: Sum(Close * Volume) / Sum(Volume) over N periods.
    """
    if len(closes) < period:
        return np.array([])
    vwma = pd.Series(closes * volumes).rolling(window=period).sum() / pd.Series(volumes).rolling(window=period).sum()
    return vwma.values[period-1:]


def technical_ratings(rsi: float, price: float, sma200: float, macd: float, signal: float) -> float:
    """
    Calculate Technical Ratings.

    Average of (RSI > 50, Price > SMA200, MACD > Signal).
    """
    score = 0.0
    if rsi > 50:
        score += 1
    if price > sma200:
        score += 1
    if macd > signal:
        score += 1
    return score / 3.0


def time_weighted_average_price(highs: np.ndarray, lows: np.ndarray, closes: np.ndarray, opens: np.ndarray) -> float:
    """
    Calculate Time Weighted Average Price (TWAP).

    Average of (Open + High + Low + Close) / 4 over the rolling window.
    """
    typical = (opens + highs + lows + closes) / 4
    return np.mean(typical)


def trading_sessions(current_time) -> List[str]:
    """
    Check if current time falls within trading sessions (UTC based).

    Returns list of active sessions: ['Asia', 'London', 'New York']
    """
    from datetime import datetime
    if isinstance(current_time, str):
        current_time = datetime.fromisoformat(current_time.replace('Z', '+00:00'))
    hour = current_time.hour
    sessions = []
    if 0 <= hour < 9:  # Asia (Tokyo)
        sessions.append('Asia')
    if 8 <= hour < 16:  # London
        sessions.append('London')
    if 13 <= hour < 21:  # New York
        sessions.append('New York')
    return sessions


def trend_strength_index(highs: np.ndarray, lows: np.ndarray, closes: np.ndarray, period: int = 14) -> np.ndarray:
    """
    Calculate Trend Strength Index.

    Abs(SMA_Fast - SMA_Slow) / SMA_Slow
    """
    fast = moving_average_simple(closes, 5)
    slow = moving_average_simple(closes, 10)
    if len(fast) == 0 or len(slow) == 0:
        return np.array([])
    min_len = min(len(fast), len(slow))
    tsi = np.abs(fast[-min_len:] - slow[-min_len:]) / slow[-min_len:]
    return tsi


def triple_exponential_moving_average(closes: np.ndarray, period: int) -> np.ndarray:
    """
    Calculate Triple EMA (TEMA).

    Formula: 3 * EMA1 - 3 * EMA2 + EMA3
    """
    if len(closes) < period * 3:
        return np.array([])
    ema1 = pd.Series(closes).ewm(span=period).mean()
    ema2 = ema1.ewm(span=period).mean()
    ema3 = ema2.ewm(span=period).mean()
    tema = 3 * ema1 - 3 * ema2 + ema3
    return tema.values[period*3 - 3:]


def stochastic_momentum_index(highs: np.ndarray, lows: np.ndarray, closes: np.ndarray, k_period: int = 14, smooth1: int = 3, smooth2: int = 3) -> np.ndarray:
    """
    Calculate Stochastic Momentum Index (SMI).
    """
    if len(highs) < k_period:
        return np.array([])
    median_price = (highs + lows) / 2
    lowest_low = pd.Series(lows).rolling(window=k_period).min()
    highest_high = pd.Series(highs).rolling(window=k_period).max()
    smi = 100 * ((closes - lowest_low) / (highest_high - lowest_low) - 0.5)
    smi_smooth1 = pd.Series(smi).rolling(window=smooth1).mean()
    smi_smooth2 = smi_smooth1.rolling(window=smooth2).mean()
    return smi_smooth2.values[k_period + smooth1 + smooth2 - 3:]


def stochastic_rsi(closes: np.ndarray, rsi_period: int = 14, stoch_period: int = 14, k_period: int = 3, d_period: int = 3) -> Tuple[np.ndarray, np.ndarray]:
    """
    Calculate Stochastic RSI.

    Returns (StochRSI_K, StochRSI_D)
    """
    rsi = relative_strength_index(closes, rsi_period)
    if len(rsi) < stoch_period:
        return np.array([]), np.array([])
    lowest_rsi = pd.Series(rsi).rolling(window=stoch_period).min()
    highest_rsi = pd.Series(rsi).rolling(window=stoch_period).max()
    stoch_rsi_k = 100 * ((rsi - lowest_rsi) / (highest_rsi - lowest_rsi))
    stoch_rsi_d = stoch_rsi_k.rolling(window=d_period).mean()
    return stoch_rsi_k.values[stoch_period-1:], stoch_rsi_d.values[stoch_period + d_period - 2:]


def multi_time_period_logic(highs: np.ndarray, lows: np.ndarray, closes: np.ndarray, opens: np.ndarray, volumes: np.ndarray, timeframes: List[int]) -> Dict[str, Dict]:
    """
    Resample RollingWindow to higher timeframes.

    Assumes 1-min data, timeframes in minutes.
    Returns dict with last closed candle for each timeframe.
    """
    result = {}
    for tf in timeframes:
        if len(closes) < tf:
            result[f'{tf}min'] = {}
            continue
        # Take last tf bars
        idx = slice(-tf, None)
        resampled_close = closes[idx][-1]
        resampled_high = np.max(highs[idx])
        resampled_low = np.min(lows[idx])
        resampled_open = opens[idx][0]
        resampled_vol = np.sum(volumes[idx])
        result[f'{tf}min'] = {
            'open': resampled_open,
            'high': resampled_high,
            'low': resampled_low,
            'close': resampled_close,
            'volume': resampled_vol
        }
    return result


def open_interest() -> float:
    """
    Return Open Interest if available; otherwise 0.0.
    """
    return 0.0  # Placeholder, as data feed may not provide OI


def price_target(closes: np.ndarray, atr: np.ndarray, multiplier: float = 1.0) -> Tuple[float, float]:
    """
    Calculate Price Target.

    Returns (target_up, target_down)
    """
    if len(atr) == 0:
        return closes[-1], closes[-1]
    return closes[-1] + atr[-1] * multiplier, closes[-1] - atr[-1] * multiplier


def rank_correlation_index(closes: np.ndarray, period: int) -> np.ndarray:
    """
    Calculate Rank Correlation Index (RCI).

    Spearman's rank correlation between time and price.
    """
    if len(closes) < period:
        return np.array([])
    result = np.zeros(len(closes) - period + 1)
    for i in range(period, len(closes) + 1):
        prices = closes[i-period:i]
        time_idx = np.arange(period)
        # Manual Spearman
        price_rank = np.argsort(np.argsort(prices))
        time_rank = np.argsort(np.argsort(time_idx))
        d = price_rank - time_rank
        result[i - period] = 1 - 6 * np.sum(d**2) / (period * (period**2 - 1))
    return result


def rci_ribbon(closes: np.ndarray, periods: List[int] = [9, 14, 21]) -> Dict[str, np.ndarray]:
    """
    Calculate RCI Ribbon.

    Returns dict with 'RCI_Short', 'RCI_Mid', 'RCI_Long'
    """
    ribbon = {}
    for i, p in enumerate(periods):
        key = ['RCI_Short', 'RCI_Mid', 'RCI_Long'][i] if i < 3 else f'RCI_{p}'
        ribbon[key] = rank_correlation_index(closes, p)
    return ribbon


def relative_vigor_index(highs: np.ndarray, lows: np.ndarray, closes: np.ndarray, opens: np.ndarray, period: int = 10) -> np.ndarray:
    """
    Calculate Relative Vigor Index (RVI).

    Formula: SMA of (Close - Open) / (High - Low)
    """
    if len(highs) < period:
        return np.array([])
    numerator = (closes - opens) / (highs - lows)
    rvi = pd.Series(numerator).rolling(window=period).mean()
    return rvi.values[period-1:]


def relative_volatility_index(highs: np.ndarray, lows: np.ndarray, period: int = 10) -> np.ndarray:
    """
    Calculate Relative Volatility Index.

    RSI of the Standard Deviation of Highs and Lows.
    """
    volatility = highs - lows
    return relative_strength_index(volatility, period)


def relative_volume_at_time(volumes: np.ndarray, current_hour: int, historical_volumes: Optional[Dict[int, np.ndarray]] = None) -> float:
    """
    Calculate Relative Volume at Time (RVOL).

    Compares current volume to average at this hour.
    """
    current_vol = np.mean(volumes)
    if historical_volumes and current_hour in historical_volumes:
        avg_vol = np.mean(historical_volumes[current_hour])
        return current_vol / avg_vol if avg_vol > 0 else 1.0
    # Fallback to recent average
    return current_vol / np.mean(volumes) if len(volumes) > 0 else 1.0


def rob_booker_intraday_pivot_points(highs: np.ndarray, lows: np.ndarray, closes: np.ndarray) -> Dict[str, float]:
    """
    Calculate Rob Booker Intraday Pivot Points based on 1-hour blocks.
    """
    if len(highs) < 60:  # Assume 60 bars = 1 hour
        return {}
    h = np.max(highs[-60:])
    l = np.min(lows[-60:])
    c = closes[-1]
    p = (h + l + c) / 3
    r1 = 2 * p - l
    s1 = 2 * p - h
    r2 = p + (h - l)
    s2 = p - (h - l)
    return {'P': p, 'R1': r1, 'S1': s1, 'R2': r2, 'S2': s2}


def rob_booker_knoxville_divergence(momentum: np.ndarray, prices: np.ndarray) -> bool:
    """
    Identify Rob Booker Knoxville Divergence.

    Bearish: Momentum falling while Price rising.
    """
    if len(momentum) < 2 or len(prices) < 2:
        return False
    return momentum[-1] < momentum[-2] and prices[-1] > prices[-2]


def rob_booker_missed_pivot_points(highs: np.ndarray, lows: np.ndarray, closes: np.ndarray, pivots: Dict[str, float]) -> List[str]:
    """
    Track Rob Booker Missed Pivot Points.

    Returns list of missed pivots.
    """
    missed = []
    current_high = np.max(highs)
    current_low = np.min(lows)
    for level, price in pivots.items():
        if level.startswith('R') and current_high < price:
            missed.append(level)
        elif level.startswith('S') and current_low > price:
            missed.append(level)
    return missed


def rob_booker_reversal(macd: np.ndarray, signal: np.ndarray, stoch_k: np.ndarray, stoch_d: np.ndarray) -> bool:
    """
    Identify Rob Booker Reversal signals.

    Based on MACD/Stochastic crossovers in extreme zones.
    """
    if len(macd) == 0 or len(signal) == 0 or len(stoch_k) == 0 or len(stoch_d) == 0:
        return False
    # Simple check: MACD cross signal and Stochastic extreme
    macd_cross = (macd[-1] > signal[-1] and macd[-2] <= signal[-2]) or (macd[-1] < signal[-1] and macd[-2] >= signal[-2])
    stoch_extreme = stoch_k[-1] < 20 or stoch_k[-1] > 80
    return macd_cross and stoch_extreme


def rob_booker_ziv_ghost_pivots(highs: np.ndarray, lows: np.ndarray, closes: np.ndarray) -> Dict[str, float]:
    """
    Calculate Rob Booker Ziv Ghost Pivots.

    Variation of pivot points.
    """
    return pivot_points_high_low(highs, lows, closes)


def rsi_divergence(closes: np.ndarray, rsi: np.ndarray) -> str:
    """
    Detect RSI Divergence.

    Returns 'Bullish Divergence', 'Bearish Divergence', or 'None'
    """
    if len(closes) < 3 or len(rsi) < 3:
        return 'None'
    # Check for divergence in last 3 points
    price_trend = closes[-1] > closes[-2] > closes[-3]
    rsi_trend = rsi[-1] > rsi[-2] > rsi[-3]
    if price_trend and not rsi_trend:
        return 'Bearish Divergence'
    if not price_trend and rsi_trend:
        return 'Bullish Divergence'
    return 'None'


def seasonality(closes: np.ndarray, current_hour: int) -> float:
    """
    Calculate Seasonality: Average return for the current hour.
    """
    if len(closes) < 24:
        return 0.0
    # Assume closes are hourly returns
    returns = np.diff(closes) / closes[:-1]
    if current_hour >= len(returns):
        return 0.0
    # Average return at this hour across days
    hourly_returns = returns[current_hour::24]
    return np.mean(hourly_returns) if len(hourly_returns) > 0 else 0.0


def smi_ergodic_indicator(closes: np.ndarray, period: int = 20) -> np.ndarray:
    """
    Calculate SMI Ergodic Indicator / Oscillator.

    Double smoothed EMA of price change.
    """
    if len(closes) < period * 2:
        return np.array([])
    pc = np.diff(closes)
    ema1 = pd.Series(pc).ewm(span=period).mean()
    ema2 = ema1.ewm(span=period).mean()
    return ema2.values[period*2 - 2:]


def smoothed_moving_average(closes: np.ndarray, period: int) -> np.ndarray:
    """
    Calculate Smoothed Moving Average (SMMA).

    Formula: (Sum - SMMA_prev + Close) / N
    """
    return calc_smma(closes, period)
