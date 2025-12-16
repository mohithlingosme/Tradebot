"""
Pattern Recognition Module for FINBOT

This module provides functions for detecting chart patterns and candlestick patterns
in financial time series data. Functions return Boolean arrays or lists of detected patterns.
"""

import numpy as np
from typing import List, Dict, Tuple, Optional, Union
from dataclasses import dataclass


@dataclass
class PatternResult:
    """Container for pattern detection results."""
    detected: bool
    strength: float = 0.0
    metadata: Dict = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


# Chart Patterns (Geometric)

def detect_flag_pennant(highs: np.ndarray, lows: np.ndarray, closes: np.ndarray,
                       lookback: int = 50, tolerance: float = 0.05) -> List[Dict]:
    """
    Detect Bullish/Bearish Flag and Pennant patterns.

    Returns list of detected patterns with metadata.
    """
    patterns = []

    if len(closes) < lookback:
        return patterns

    # Look for pole (strong move) followed by consolidation
    for i in range(lookback, len(closes)):
        # Check for strong upward move (bullish pole)
        pole_start = i - lookback
        pole_move = (closes[i-1] - closes[pole_start]) / closes[pole_start]

        if pole_move > 0.05:  # 5% move
            # Check for consolidation (flag/pennant)
            flag_high = np.max(highs[pole_start:i])
            flag_low = np.min(lows[pole_start:i])

            # Flag: parallel trendlines, Pennant: converging
            if flag_high > closes[i-1] * (1 - tolerance) and flag_low < closes[i-1] * (1 + tolerance):
                pattern_type = "bullish_flag" if pole_move > 0 else "bearish_flag"
                patterns.append({
                    'type': pattern_type,
                    'index': i,
                    'strength': abs(pole_move),
                    'pole_start': pole_start,
                    'pole_end': i-1
                })

    return patterns


def detect_double_top_bottom(highs: np.ndarray, lows: np.ndarray, closes: np.ndarray,
                           lookback: int = 100, tolerance: float = 0.03) -> List[Dict]:
    """
    Detect Double Top/Bottom patterns.

    Returns list of detected patterns.
    """
    patterns = []

    if len(closes) < lookback:
        return patterns

    for i in range(lookback, len(closes)):
        window_highs = highs[i-lookback:i]
        window_lows = lows[i-lookback:i]

        # Find peaks and valleys
        peaks = []
        valleys = []

        for j in range(1, len(window_highs)-1):
            if window_highs[j] > window_highs[j-1] and window_highs[j] > window_highs[j+1]:
                peaks.append((j + i - lookback, window_highs[j]))
            if window_lows[j] < window_lows[j-1] and window_lows[j] < window_lows[j+1]:
                valleys.append((j + i - lookback, window_lows[j]))

        # Check for double top
        if len(peaks) >= 2:
            recent_peaks = peaks[-2:]
            if abs(recent_peaks[0][1] - recent_peaks[1][1]) / recent_peaks[0][1] < tolerance:
                patterns.append({
                    'type': 'double_top',
                    'index': i,
                    'peaks': recent_peaks,
                    'strength': 1.0
                })

        # Check for double bottom
        if len(valleys) >= 2:
            recent_valleys = valleys[-2:]
            if abs(recent_valleys[0][1] - recent_valleys[1][1]) / recent_valleys[0][1] < tolerance:
                patterns.append({
                    'type': 'double_bottom',
                    'index': i,
                    'valleys': recent_valleys,
                    'strength': 1.0
                })

    return patterns


def detect_triangle(highs: np.ndarray, lows: np.ndarray, closes: np.ndarray,
                   lookback: int = 50) -> List[Dict]:
    """
    Detect Ascending/Descending/Symmetrical Triangle patterns.

    Returns list of detected patterns.
    """
    patterns = []

    if len(closes) < lookback:
        return patterns

    for i in range(lookback, len(closes)):
        window_highs = highs[i-lookback:i]
        window_lows = lows[i-lookback:i]

        # Fit trendlines
        x = np.arange(len(window_highs))

        # Upper trendline (resistance)
        try:
            upper_slope, upper_intercept = np.polyfit(x, window_highs, 1)
            upper_trend = upper_slope * x + upper_intercept
        except:
            continue

        # Lower trendline (support)
        try:
            lower_slope, lower_intercept = np.polyfit(x, window_lows, 1)
            lower_trend = lower_slope * x + lower_intercept
        except:
            continue

        # Check triangle types
        if upper_slope < 0 and lower_slope > 0:
            pattern_type = 'symmetrical_triangle'
        elif upper_slope < 0 and lower_slope < 0:
            pattern_type = 'descending_triangle'
        elif upper_slope > 0 and lower_slope > 0:
            pattern_type = 'ascending_triangle'
        else:
            continue

        # Check if price is within triangle
        within_triangle = np.all((window_lows >= lower_trend * 0.98) &
                               (window_highs <= upper_trend * 1.02))

        if within_triangle:
            patterns.append({
                'type': pattern_type,
                'index': i,
                'upper_slope': upper_slope,
                'lower_slope': lower_slope,
                'strength': 1.0
            })

    return patterns


def detect_wedge(highs: np.ndarray, lows: np.ndarray, closes: np.ndarray,
                lookback: int = 50) -> List[Dict]:
    """
    Detect Falling/Rising Wedge patterns.

    Returns list of detected patterns.
    """
    patterns = []

    if len(closes) < lookback:
        return patterns

    for i in range(lookback, len(closes)):
        window_highs = highs[i-lookback:i]
        window_lows = lows[i-lookback:i]
        x = np.arange(len(window_highs))

        # Fit trendlines
        try:
            upper_slope, upper_intercept = np.polyfit(x, window_highs, 1)
            lower_slope, lower_intercept = np.polyfit(x, window_lows, 1)
        except:
            continue

        # Wedge: both lines converging
        if abs(upper_slope) > 0.001 and abs(lower_slope) > 0.001:
            if (upper_slope < 0 and lower_slope < 0) or (upper_slope > 0 and lower_slope > 0):
                pattern_type = 'falling_wedge' if upper_slope < 0 else 'rising_wedge'

                patterns.append({
                    'type': pattern_type,
                    'index': i,
                    'upper_slope': upper_slope,
                    'lower_slope': lower_slope,
                    'strength': 1.0
                })

    return patterns


def detect_cup_handle(highs: np.ndarray, lows: np.ndarray, closes: np.ndarray,
                     lookback: int = 100) -> List[Dict]:
    """
    Detect Cup and Handle patterns.

    Returns list of detected patterns.
    """
    patterns = []

    if len(closes) < lookback:
        return patterns

    for i in range(lookback, len(closes)):
        window_closes = closes[i-lookback:i]

        # Find cup shape (U-shape)
        min_idx = np.argmin(window_closes)
        left_side = window_closes[:min_idx]
        right_side = window_closes[min_idx:]

        if len(left_side) < 10 or len(right_side) < 10:
            continue

        # Check if it's a cup (both sides roughly symmetrical)
        left_avg = np.mean(left_side)
        right_avg = np.mean(right_side)
        bottom = window_closes[min_idx]

        # Cup criteria: sides higher than bottom, roughly equal height
        if (left_avg > bottom * 1.05 and right_avg > bottom * 1.05 and
            abs(left_avg - right_avg) / left_avg < 0.1):

            # Check for handle (smaller consolidation after cup)
            handle_start = i - min(20, len(right_side)//2)
            handle_closes = closes[handle_start:i]

            if len(handle_closes) > 5:
                handle_high = np.max(handle_closes)
                handle_low = np.min(handle_closes)
                cup_high = np.max(window_closes)

                # Handle should be smaller than cup
                if handle_high < cup_high * 0.95:
                    patterns.append({
                        'type': 'cup_handle',
                        'index': i,
                        'cup_bottom_index': i - lookback + min_idx,
                        'handle_start': handle_start,
                        'strength': 1.0
                    })

    return patterns


# Candlestick Patterns

def detect_doji(opens: np.ndarray, highs: np.ndarray, lows: np.ndarray, closes: np.ndarray,
               body_threshold: float = 0.1) -> np.ndarray:
    """
    Detect Doji patterns (all types).

    Returns boolean array where True indicates a Doji.
    """
    if len(opens) != len(closes):
        return np.array([])

    body_size = np.abs(closes - opens)
    total_range = highs - lows

    # Avoid division by zero
    total_range = np.where(total_range == 0, 1e-8, total_range)

    body_ratio = body_size / total_range

    # Doji: body is very small relative to total range
    return body_ratio < body_threshold


def detect_hammer(opens: np.ndarray, highs: np.ndarray, lows: np.ndarray, closes: np.ndarray) -> np.ndarray:
    """
    Detect Hammer and Hanging Man patterns.

    Returns boolean array where True indicates a Hammer/Hanging Man.
    """
    if len(opens) != len(closes):
        return np.array([])

    body_size = np.abs(closes - opens)
    upper_shadow = highs - np.maximum(opens, closes)
    lower_shadow = np.minimum(opens, closes) - lows
    total_range = highs - lows

    # Avoid division by zero
    total_range = np.where(total_range == 0, 1e-8, total_range)

    # Hammer: small body, long lower shadow, small upper shadow
    hammer_condition = (
        (body_size / total_range < 0.3) &
        (lower_shadow / total_range > 0.6) &
        (upper_shadow / total_range < 0.1)
    )

    return hammer_condition


def detect_engulfing(opens: np.ndarray, highs: np.ndarray, lows: np.ndarray, closes: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """
    Detect Bullish and Bearish Engulfing patterns.

    Returns tuple of (bullish_engulfing, bearish_engulfing) boolean arrays.
    """
    if len(opens) < 2:
        return np.array([]), np.array([])

    # Previous candle
    prev_open = opens[:-1]
    prev_close = closes[:-1]
    prev_high = highs[:-1]
    prev_low = lows[:-1]

    # Current candle
    curr_open = opens[1:]
    curr_close = closes[1:]
    curr_high = highs[1:]
    curr_low = lows[1:]

    # Bullish engulfing: previous bearish, current bullish, current engulfs previous
    bullish = (
        (prev_close < prev_open) &  # Previous bearish
        (curr_close > curr_open) &  # Current bullish
        (curr_open <= prev_close) &
        (curr_close >= prev_open)
    )

    # Bearish engulfing: previous bullish, current bearish, current engulfs previous
    bearish = (
        (prev_close > prev_open) &  # Previous bullish
        (curr_close < curr_open) &  # Current bearish
        (curr_open >= prev_close) &
        (curr_close <= prev_open)
    )

    return bullish, bearish


def detect_morning_star(opens: np.ndarray, highs: np.ndarray, lows: np.ndarray, closes: np.ndarray) -> np.ndarray:
    """
    Detect Morning Star pattern.

    Returns boolean array where True indicates a Morning Star.
    """
    if len(opens) < 3:
        return np.array([])

    # Three candles: 1st bearish, 2nd small body (star), 3rd bullish
    first_bearish = closes[:-2] < opens[:-2]
    third_bullish = closes[2:] > opens[2:]

    # Second candle (star): small body
    star_body = np.abs(closes[1:-1] - opens[1:-1])
    star_range = highs[1:-1] - lows[1:-1]
    star_condition = star_body / star_range < 0.3

    # Gap conditions (simplified)
    morning_star = first_bearish & star_condition & third_bullish

    return morning_star


def detect_evening_star(opens: np.ndarray, highs: np.ndarray, lows: np.ndarray, closes: np.ndarray) -> np.ndarray:
    """
    Detect Evening Star pattern.

    Returns boolean array where True indicates an Evening Star.
    """
    if len(opens) < 3:
        return np.array([])

    # Three candles: 1st bullish, 2nd small body (star), 3rd bearish
    first_bullish = closes[:-2] > opens[:-2]
    third_bearish = closes[2:] < opens[2:]

    # Second candle (star): small body
    star_body = np.abs(closes[1:-1] - opens[1:-1])
    star_range = highs[1:-1] - lows[1:-1]
    star_condition = star_body / star_range < 0.3

    evening_star = first_bullish & star_condition & third_bearish

    return evening_star


def detect_three_white_soldiers(opens: np.ndarray, highs: np.ndarray, lows: np.ndarray, closes: np.ndarray) -> np.ndarray:
    """
    Detect Three White Soldiers pattern.

    Returns boolean array where True indicates Three White Soldiers.
    """
    if len(opens) < 3:
        return np.array([])

    # Three consecutive bullish candles with increasing closes
    bullish1 = closes[:-2] > opens[:-2]
    bullish2 = closes[1:-1] > opens[1:-1]
    bullish3 = closes[2:] > opens[2:]

    increasing_closes = (closes[1:-1] > closes[:-2]) & (closes[2:] > closes[1:-1])

    return bullish1 & bullish2 & bullish3 & increasing_closes


def detect_three_black_crows(opens: np.ndarray, highs: np.ndarray, lows: np.ndarray, closes: np.ndarray) -> np.ndarray:
    """
    Detect Three Black Crows pattern.

    Returns boolean array where True indicates Three Black Crows.
    """
    if len(opens) < 3:
        return np.array([])

    # Three consecutive bearish candles with decreasing closes
    bearish1 = closes[:-2] < opens[:-2]
    bearish2 = closes[1:-1] < opens[1:-1]
    bearish3 = closes[2:] < opens[2:]

    decreasing_closes = (closes[1:-1] < closes[:-2]) & (closes[2:] < closes[1:-1])

    return bearish1 & bearish2 & bearish3 & decreasing_closes


def detect_piercing_line(opens: np.ndarray, highs: np.ndarray, lows: np.ndarray, closes: np.ndarray) -> np.ndarray:
    """
    Detect Piercing Line pattern.

    Returns boolean array where True indicates a Piercing Line.
    """
    if len(opens) < 2:
        return np.array([])

    prev_bearish = closes[:-1] < opens[:-1]
    curr_bullish = closes[1:] > opens[1:]

    # Piercing: opens below prev low, closes above prev midpoint
    prev_midpoint = (opens[:-1] + closes[:-1]) / 2

    piercing = (
        prev_bearish &
        curr_bullish &
        (opens[1:] < closes[:-1]) &
        (closes[1:] > prev_midpoint) &
        (closes[1:] < opens[:-1])
    )

    return piercing


def detect_dark_cloud_cover(opens: np.ndarray, highs: np.ndarray, lows: np.ndarray, closes: np.ndarray) -> np.ndarray:
    """
    Detect Dark Cloud Cover pattern.

    Returns boolean array where True indicates a Dark Cloud Cover.
    """
    if len(opens) < 2:
        return np.array([])

    prev_bullish = closes[:-1] > opens[:-1]
    curr_bearish = closes[1:] < opens[1:]

    # Dark cloud: opens above prev high, closes below prev midpoint
    prev_midpoint = (opens[:-1] + closes[:-1]) / 2

    dark_cloud = (
        prev_bullish &
        curr_bearish &
        (opens[1:] > closes[:-1]) &
        (closes[1:] < prev_midpoint) &
        (closes[1:] > opens[:-1])
    )

    return dark_cloud


def detect_harami(opens: np.ndarray, highs: np.ndarray, lows: np.ndarray, closes: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """
    Detect Harami patterns (Bullish and Bearish).

    Returns tuple of (bullish_harami, bearish_harami) boolean arrays.
    """
    if len(opens) < 2:
        return np.array([]), np.array([])

    prev_body_high = np.maximum(opens[:-1], closes[:-1])
    prev_body_low = np.minimum(opens[:-1], closes[:-1])
    curr_body_high = np.maximum(opens[1:], closes[1:])
    curr_body_low = np.minimum(opens[1:], closes[1:])

    # Bullish Harami: previous bearish, current bullish, current body inside previous body
    bullish_harami = (
        (closes[:-1] < opens[:-1]) &  # Previous bearish
        (closes[1:] > opens[1:]) &    # Current bullish
        (curr_body_high <= prev_body_high) &
        (curr_body_low >= prev_body_low)
    )

    # Bearish Harami: previous bullish, current bearish, current body inside previous body
    bearish_harami = (
        (closes[:-1] > opens[:-1]) &  # Previous bullish
        (closes[1:] < opens[1:]) &    # Current bearish
        (curr_body_high <= prev_body_high) &
        (curr_body_low >= prev_body_low)
    )

    return bullish_harami, bearish_harami


def detect_marubozu(opens: np.ndarray, highs: np.ndarray, lows: np.ndarray, closes: np.ndarray,
                   shadow_threshold: float = 0.05) -> Tuple[np.ndarray, np.ndarray]:
    """
    Detect Marubozu patterns (White and Black).

    Returns tuple of (white_marubozu, black_marubozu) boolean arrays.
    """
    body_size = np.abs(closes - opens)
    total_range = highs - lows

    # Avoid division by zero
    total_range = np.where(total_range == 0, 1e-8, total_range)

    upper_shadow = highs - np.maximum(opens, closes)
    lower_shadow = np.minimum(opens, closes) - lows

    shadow_ratio = (upper_shadow + lower_shadow) / total_range

    # Marubozu: very small shadows relative to body
    marubozu = shadow_ratio < shadow_threshold

    white_marubozu = marubozu & (closes > opens)
    black_marubozu = marubozu & (closes < opens)

    return white_marubozu, black_marubozu


def detect_spinning_top(opens: np.ndarray, highs: np.ndarray, lows: np.ndarray, closes: np.ndarray) -> np.ndarray:
    """
    Detect Spinning Top pattern.

    Returns boolean array where True indicates a Spinning Top.
    """
    body_size = np.abs(closes - opens)
    upper_shadow = highs - np.maximum(opens, closes)
    lower_shadow = np.minimum(opens, closes) - lows
    total_range = highs - lows

    # Avoid division by zero
    total_range = np.where(total_range == 0, 1e-8, total_range)

    # Spinning top: small body, long upper and lower shadows
    spinning_top = (
        (body_size / total_range < 0.3) &
        (upper_shadow / total_range > 0.3) &
        (lower_shadow / total_range > 0.3)
    )

    return spinning_top


def detect_abandoned_baby(opens: np.ndarray, highs: np.ndarray, lows: np.ndarray, closes: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """
    Detect Abandoned Baby patterns.

    Returns tuple of (bullish_abandoned_baby, bearish_abandoned_baby) boolean arrays.
    """
    if len(opens) < 3:
        return np.array([]), np.array([])

    # First candle
    first_bearish = closes[:-2] < opens[:-2]
    first_bullish = closes[:-2] > opens[:-2]

    # Third candle
    third_bullish = closes[2:] > opens[2:]
    third_bearish = closes[2:] < opens[2:]

    # Second candle (baby): doji with gap
    middle_doji = detect_doji(opens[1:-1], highs[1:-1], lows[1:-1], closes[1:-1])

    # Gap conditions (simplified)
    bullish_baby = first_bearish & middle_doji & third_bullish
    bearish_baby = first_bullish & middle_doji & third_bearish

    return bullish_baby, bearish_baby


def detect_kicking(opens: np.ndarray, highs: np.ndarray, lows: np.ndarray, closes: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """
    Detect Kicking patterns.

    Returns tuple of (bullish_kicking, bearish_kicking) boolean arrays.
    """
    if len(opens) < 2:
        return np.array([]), np.array([])

    prev_marubozu_white, prev_marubozu_black = detect_marubozu(opens[:-1], highs[:-1], lows[:-1], closes[:-1])
    curr_marubozu_white, curr_marubozu_black = detect_marubozu(opens[1:], highs[1:], lows[1:], closes[1:])

    # Bullish kicking: black marubozu followed by white marubozu with gap
    bullish_kicking = prev_marubozu_black & curr_marubozu_white

    # Bearish kicking: white marubozu followed by black marubozu with gap
    bearish_kicking = prev_marubozu_white & curr_marubozu_black

    return bullish_kicking, bearish_kicking


def detect_tweezer_top_bottom(highs: np.ndarray, lows: np.ndarray, closes: np.ndarray,
                             tolerance: float = 0.01) -> Tuple[np.ndarray, np.ndarray]:
    """
    Detect Tweezer Top and Bottom patterns.

    Returns tuple of (tweezer_top, tweezer_bottom) boolean arrays.
    """
    if len(highs) < 2:
        return np.array([]), np.array([])

    # Tweezer top: two candles with same high
    tweezer_top = np.abs(highs[1:] - highs[:-1]) / highs[:-1] < tolerance

    # Tweezer bottom: two candles with same low
    tweezer_bottom = np.abs(lows[1:] - lows[:-1]) / lows[:-1] < tolerance

    return tweezer_top, tweezer_bottom


def detect_rising_falling_window(opens: np.ndarray, highs: np.ndarray, lows: np.ndarray, closes: np.ndarray,
                                gap_threshold: float = 0.02) -> Tuple[np.ndarray, np.ndarray]:
    """
    Detect Rising and Falling Window (Gap) patterns.

    Returns tuple of (rising_window, falling_window) boolean arrays.
    """
    if len(opens) < 2:
        return np.array([]), np.array([])

    # Rising window: gap up between candles
    prev_high = highs[:-1]
    curr_low = lows[1:]
    rising_window = (curr_low - prev_high) / prev_high > gap_threshold

    # Falling window: gap down between candles
    prev_low = lows[:-1]
    curr_high = highs[1:]
    falling_window = (prev_low - curr_high) / prev_low > gap_threshold

    return rising_window, falling_window


def detect_three_methods(opens: np.ndarray, highs: np.ndarray, lows: np.ndarray, closes: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """
    Detect Rising and Falling Three Methods patterns.

    Returns tuple of (rising_three_methods, falling_three_methods) boolean arrays.
    """
    if len(opens) < 5:
        return np.array([]), np.array([])

    # Rising three methods: long white, three small blacks, long white
    # Simplified version - check for pattern of 5 candles
    first_bullish = closes[:-4] > opens[:-4]
    last_bullish = closes[4:] > opens[4:]

    # Middle three candles should be small and contained within first and last
    middle_highs = np.max(highs[1:-3], axis=0)
    middle_lows = np.min(lows[1:-3], axis=0)

    rising_methods = (
        first_bullish &
        last_bullish &
        (middle_highs < highs[:-4]) &
        (middle_lows > lows[:-4])
    )

    # Falling three methods: long black, three small whites, long black
    first_bearish = closes[:-4] < opens[:-4]
    last_bearish = closes[4:] < opens[4:]

    falling_methods = (
        first_bearish &
        last_bearish &
        (middle_highs < highs[:-4]) &
        (middle_lows > lows[:-4])
    )

    return rising_methods, falling_methods


def detect_tasuki_gap(opens: np.ndarray, highs: np.ndarray, lows: np.ndarray, closes: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """
    Detect Upside and Downside Tasuki Gap patterns.

    Returns tuple of (upside_tasuki, downside_tasuki) boolean arrays.
    """
    if len(opens) < 3:
        return np.array([]), np.array([])

    # First two candles form a window (gap)
    rising_window, falling_window = detect_rising_falling_window(opens[:-1], highs[:-1], lows[:-1], closes[:-1])

    # Third candle
    third_bullish = closes[2:] > opens[2:]
    third_bearish = closes[2:] < opens[2:]

    # Upside Tasuki: rising window, third bullish candle closes gap
    upside_tasuki = rising_window[:-1] & third_bullish & (closes[2:] > (opens[1:-1] + closes[1:-1]) / 2)

    # Downside Tasuki: falling window, third bearish candle closes gap
    downside_tasuki = falling_window[:-1] & third_bearish & (closes[2:] < (opens[1:-1] + closes[1:-1]) / 2)

    return upside_tasuki, downside_tasuki


# Helper functions

def get_pattern_strength(opens: np.ndarray, highs: np.ndarray, lows: np.ndarray, closes: np.ndarray,
                        pattern_func, *args, **kwargs) -> float:
    """
    Calculate pattern strength based on volume and price action.

    This is a generic function that can be used with any pattern detection function.
    """
    detected = pattern_func(opens, highs, lows, closes, *args, **kwargs)

    if isinstance(detected, tuple):
        detected = detected[0]  # Take first element if tuple

    if len(detected) == 0 or not np.any(detected):
        return 0.0

    # Simple strength calculation based on how many patterns detected
    pattern_count = np.sum(detected)
    total_candles = len(detected)

    return min(pattern_count / total_candles * 100, 100.0)


def scan_all_patterns(opens: np.ndarray, highs: np.ndarray, lows: np.ndarray, closes: np.ndarray) -> Dict[str, Union[np.ndarray, List]]:
    """
    Scan for all supported patterns and return results.

    Returns dictionary with pattern names as keys and detection results as values.
    """
    results = {}

    # Candlestick patterns
    results['doji'] = detect_doji(opens, highs, lows, closes)
    results['hammer'] = detect_hammer(opens, highs, lows, closes)
    results['spinning_top'] = detect_spinning_top(opens, highs, lows, closes)

    bullish_engulfing, bearish_engulfing = detect_engulfing(opens, highs, lows, closes)
    results['bullish_engulfing'] = bullish_engulfing
    results['bearish_engulfing'] = bearish_engulfing

    results['morning_star'] = detect_morning_star(opens, highs, lows, closes)
    results['evening_star'] = detect_evening_star(opens, highs, lows, closes)

    results['three_white_soldiers'] = detect_three_white_soldiers(opens, highs, lows, closes)
    results['three_black_crows'] = detect_three_black_crows(opens, highs, lows, closes)

    results['piercing_line'] = detect_piercing_line(opens, highs, lows, closes)
    results['dark_cloud_cover'] = detect_dark_cloud_cover(opens, highs, lows, closes)

    bullish_harami, bearish_harami = detect_harami(opens, highs, lows, closes)
    results['bullish_harami'] = bullish_harami
    results['bearish_harami'] = bearish_harami

    white_marubozu, black_marubozu = detect_marubozu(opens, highs, lows, closes)
    results['white_marubozu'] = white_marubozu
    results['black_marubozu'] = black_marubozu

    bullish_abandoned, bearish_abandoned = detect_abandoned_baby(opens, highs, lows, closes)
    results['bullish_abandoned_baby'] = bullish_abandoned
    results['bearish_abandoned_baby'] = bearish_abandoned

    bullish_kicking, bearish_kicking = detect_kicking(opens, highs, lows, closes)
    results['bullish_kicking'] = bullish_kicking
    results['bearish_kicking'] = bearish_kicking

    tweezer_top, tweezer_bottom = detect_tweezer_top_bottom(highs, lows, closes)
    results['tweezer_top'] = tweezer_top
    results['tweezer_bottom'] = tweezer_bottom

    rising_window, falling_window = detect_rising_falling_window(opens, highs, lows, closes)
    results['rising_window'] = rising_window
    results['falling_window'] = falling_window

    rising_methods, falling_methods = detect_three_methods(opens, highs, lows, closes)
    results['rising_three_methods'] = rising_methods
    results['falling_three_methods'] = falling_methods

    upside_tasuki, downside_tasuki = detect_tasuki_gap(opens, highs, lows, closes)
    results['upside_tasuki_gap'] = upside_tasuki
    results['downside_tasuki_gap'] = downside_tasuki

    # Chart patterns (return lists of dictionaries)
    results['flags_pennants'] = detect_flag_pennant(highs, lows, closes)
    results['double_patterns'] = detect_double_top_bottom(highs, lows, closes)
    results['triangles'] = detect_triangle(highs, lows, closes)
    results['wedges'] = detect_wedge(highs, lows, closes)
    results['cup_handles'] = detect_cup_handle(highs, lows, closes)

    return results
