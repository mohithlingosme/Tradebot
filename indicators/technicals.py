"""
Technical Indicators Module for FINBOT

This module provides comprehensive technical analysis indicators implemented as
stateless functions using numpy and pandas for vectorized calculations.
"""

import numpy as np
import pandas as pd
from typing import Tuple, Dict, List, Optional, Union
from dataclasses import dataclass
from datetime import datetime, timedelta
import math


# Volume & Breadth Indicators

def twenty_four_hour_volume(volumes: np.ndarray) -> float:
    """Calculate 24-hour volume (assuming 1-min bars)."""
    if len(volumes) < 1440:
        return np.sum(volumes)
    return np.sum(volumes[-1440:])


def accumulation_distribution(highs: np.ndarray, lows: np.ndarray,
                             closes: np.ndarray, volumes: np.ndarray) -> np.ndarray:
    """Calculate Chaikin Accumulation/Distribution Line."""
    hl_diff = highs - lows
    hl_diff = np.where(hl_diff == 0, 1e-8, hl_diff)
    ad_values = ((closes - lows) - (highs - closes)) / hl_diff * volumes
    return np.cumsum(ad_values)


def advance_decline_line(advances: List[float], declines: List[float]) -> np.ndarray:
    """Calculate Advance-Decline Line."""
    adv_arr = np.array(advances)
    dec_arr = np.array(declines)
    return np.cumsum(adv_arr - dec_arr)


def advance_decline_ratio(advances: List[float], declines: List[float]) -> np.ndarray:
    """Calculate Advance-Decline Ratio."""
    adv_arr = np.array(advances)
    dec_arr = np.array(declines)
    dec_arr = np.where(dec_arr == 0, 1e-8, dec_arr)
    return adv_arr / dec_arr


def cumulative_volume_delta(volumes: np.ndarray, closes: np.ndarray, opens: np.ndarray) -> np.ndarray:
    """Calculate Cumulative Volume Delta."""
    signs = np.sign(closes - opens)
    return np.cumsum(volumes * signs)


def cumulative_volume_index(volumes: np.ndarray, closes: np.ndarray, opens: np.ndarray) -> np.ndarray:
    """Calculate Cumulative Volume Index."""
    signs = np.sign(closes - opens)
    return np.cumsum(volumes * signs)


def net_volume(volumes: np.ndarray, closes: np.ndarray, opens: np.ndarray) -> np.ndarray:
    """Calculate Net Volume."""
    signs = np.sign(closes - opens)
    return np.cumsum(volumes * signs)


def on_balance_volume(closes: np.ndarray, volumes: np.ndarray) -> np.ndarray:
    """Calculate On Balance Volume."""
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


def up_down_volume(volumes: np.ndarray, closes: np.ndarray, opens: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """Calculate Up/Down Volume."""
    up_vol = np.where(closes > opens, volumes, 0)
    down_vol = np.where(closes < opens, volumes, 0)
    return np.cumsum(up_vol), np.cumsum(down_vol)


def volume_oscillator(volumes: np.ndarray, short_period: int = 12, long_period: int = 26) -> np.ndarray:
    """Calculate Volume Oscillator."""
    if len(volumes) < long_period:
        return np.array([])

    short_ma = pd.Series(volumes).rolling(window=short_period).mean()
    long_ma = pd.Series(volumes).rolling(window=long_period).mean()
    vo = ((short_ma - long_ma) / long_ma) * 100
    return vo.values[long_period-1:]


def volume_weighted_moving_average(closes: np.ndarray, volumes: np.ndarray, period: int) -> np.ndarray:
    """Calculate Volume Weighted Moving Average."""
    if len(closes) < period:
        return np.array([])
    vwma = pd.Series(closes * volumes).rolling(window=period).sum() / pd.Series(volumes).rolling(window=period).sum()
    return vwma.values[period-1:]


def ease_of_movement(highs: np.ndarray, lows: np.ndarray, volumes: np.ndarray, period: int = 14) -> np.ndarray:
    """Calculate Ease of Movement."""
    if len(highs) < period:
        return np.array([])

    distance = ((highs + lows) / 2 - (np.roll(highs + lows, 1) / 2)) / ((highs - lows) / volumes)
    distance = distance[1:]  # Remove first NaN
    ema = pd.Series(distance).ewm(span=period).mean()
    return ema.values[period-1:]


def elder_force_index(closes: np.ndarray, volumes: np.ndarray, period: int = 13) -> np.ndarray:
    """Calculate Elder Force Index."""
    if len(closes) < period + 1:
        return np.array([])

    force = (closes[1:] - closes[:-1]) * volumes[1:]
    ema = pd.Series(force).ewm(span=period).mean()
    return ema.values[period-1:]


def money_flow_index(highs: np.ndarray, lows: np.ndarray, closes: np.ndarray, volumes: np.ndarray, period: int = 14) -> np.ndarray:
    """Calculate Money Flow Index."""
    if len(highs) < period + 1:
        return np.array([])

    typical_price = (highs + lows + closes) / 3
    money_flow = typical_price * volumes

    positive_flow = np.where(typical_price[1:] > typical_price[:-1], money_flow[1:], 0)
    negative_flow = np.where(typical_price[1:] < typical_price[:-1], money_flow[1:], 0)

    pos_mf = pd.Series(positive_flow).rolling(window=period).sum()
    neg_mf = pd.Series(negative_flow).rolling(window=period).sum()

    mfr = pos_mf / neg_mf
    mfr = mfr.replace([np.inf, -np.inf], np.nan).fillna(0)
    mfi = 100 - (100 / (1 + mfr))
    return mfi.values[period-1:]


def price_volume_trend(closes: np.ndarray, volumes: np.ndarray) -> np.ndarray:
    """Calculate Price Volume Trend."""
    if len(closes) < 2:
        return np.array([])

    pvt = np.zeros(len(closes))
    pvt[0] = 0

    for i in range(1, len(closes)):
        change = (closes[i] - closes[i-1]) / closes[i-1]
        pvt[i] = pvt[i-1] + volumes[i] * change

    return pvt


def negative_volume_index(closes: np.ndarray, volumes: np.ndarray) -> np.ndarray:
    """Calculate Negative Volume Index."""
    if len(closes) < 2:
        return np.array([])

    nvi = np.zeros(len(closes))
    nvi[0] = 1000  # Starting value

    for i in range(1, len(closes)):
        if volumes[i] < volumes[i-1]:
            nvi[i] = nvi[i-1] + (closes[i] - closes[i-1]) / closes[i-1] * nvi[i-1]
        else:
            nvi[i] = nvi[i-1]

    return nvi


def positive_volume_index(closes: np.ndarray, volumes: np.ndarray) -> np.ndarray:
    """Calculate Positive Volume Index."""
    if len(closes) < 2:
        return np.array([])

    pvi = np.zeros(len(closes))
    pvi[0] = 1000  # Starting value

    for i in range(1, len(closes)):
        if volumes[i] > volumes[i-1]:
            pvi[i] = pvi[i-1] + (closes[i] - closes[i-1]) / closes[i-1] * pvi[i-1]
        else:
            pvi[i] = pvi[i-1]

    return pvi


# Moving Averages & Trends

def arnaud_legoux_ma(prices: np.ndarray, window: int, offset: float = 0.85, sigma: float = 6.0) -> np.ndarray:
    """Calculate Arnaud Legoux Moving Average."""
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


def hull_moving_average(closes: np.ndarray, period: int) -> np.ndarray:
    """Calculate Hull Moving Average."""
    if len(closes) < period:
        return np.array([])

    # Calculate weighted moving averages
    wma_half = pd.Series(closes).rolling(window=period//2).apply(lambda x: np.sum(x * np.arange(1, len(x)+1)) / np.sum(np.arange(1, len(x)+1)), raw=False)
    wma_full = pd.Series(closes).rolling(window=period).apply(lambda x: np.sum(x * np.arange(1, len(x)+1)) / np.sum(np.arange(1, len(x)+1)), raw=False)

    # Raw HMA
    raw_hma = 2 * wma_half - wma_full

    # Smooth the HMA
    sqrt_period = int(np.sqrt(period))
    hma = raw_hma.rolling(window=sqrt_period).apply(lambda x: np.sum(x * np.arange(1, len(x)+1)) / np.sum(np.arange(1, len(x)+1)), raw=False)

    return hma.values[period-1:]


def least_squares_moving_average(closes: np.ndarray, period: int) -> np.ndarray:
    """Calculate Least Squares Moving Average (Linear Regression)."""
    if len(closes) < period:
        return np.array([])

    result = np.zeros(len(closes) - period + 1)
    x = np.arange(period)

    for i in range(period, len(closes) + 1):
        y = closes[i-period:i]
        slope, intercept = np.polyfit(x, y, 1)
        result[i - period] = intercept + slope * (period - 1)

    return result


def mcginley_dynamic(closes: np.ndarray, period: int) -> np.ndarray:
    """Calculate McGinley Dynamic."""
    if len(closes) < 1:
        return np.array([])

    md = np.zeros(len(closes))
    md[0] = closes[0]
    for i in range(1, len(closes)):
        md[i] = md[i-1] + (closes[i] - md[i-1]) / (0.6 * period)
    return md


def smoothed_moving_average(closes: np.ndarray, period: int) -> np.ndarray:
    """Calculate Smoothed Moving Average."""
    if len(closes) < period:
        return np.array([])
    smma = np.zeros(len(closes))
    smma[period-1] = np.mean(closes[:period])
    for i in range(period, len(closes)):
        smma[i] = (smma[i-1] * (period - 1) + closes[i]) / period
    return smma[period-1:]


def triple_exponential_moving_average(closes: np.ndarray, period: int) -> np.ndarray:
    """Calculate Triple EMA."""
    if len(closes) < period * 3:
        return np.array([])
    ema1 = pd.Series(closes).ewm(span=period).mean()
    ema2 = ema1.ewm(span=period).mean()
    ema3 = ema2.ewm(span=period).mean()
    tema = 3 * ema1 - 3 * ema2 + ema3
    return tema.values[period*3 - 3:]


def trix(closes: np.ndarray, period: int = 15) -> np.ndarray:
    """Calculate TRIX."""
    if len(closes) < period * 3:
        return np.array([])
    ema1 = pd.Series(closes).ewm(span=period).mean()
    ema2 = ema1.ewm(span=period).mean()
    ema3 = ema2.ewm(span=period).mean()
    trix = (ema3 - ema3.shift(1)) / ema3.shift(1) * 100
    return trix.values[period*3 - 2:]


def moving_average_ribbon(closes: np.ndarray, periods: List[int]) -> Dict[int, np.ndarray]:
    """Calculate Moving Average Ribbon."""
    ribbon = {}
    for period in periods:
        ribbon[period] = pd.Series(closes).rolling(window=period).mean().values[period-1:]
    return ribbon


def median_price(highs: np.ndarray, lows: np.ndarray) -> np.ndarray:
    """Calculate Median Price."""
    return (highs + lows) / 2


def visible_average_price(highs: np.ndarray, lows: np.ndarray, closes: np.ndarray) -> float:
    """Calculate Visible Average Price."""
    typical = (highs + lows + closes) / 3
    return np.mean(typical)


def time_weighted_average_price(highs: np.ndarray, lows: np.ndarray, closes: np.ndarray, opens: np.ndarray) -> float:
    """Calculate Time Weighted Average Price."""
    typical = (opens + highs + lows + closes) / 4
    return np.mean(typical)


def volume_weighted_average_price(highs: np.ndarray, lows: np.ndarray, closes: np.ndarray, volumes: np.ndarray) -> np.ndarray:
    """Calculate Volume Weighted Average Price."""
    typical_price = (highs + lows + closes) / 3
    vwap = np.cumsum(typical_price * volumes) / np.cumsum(volumes)
    return vwap


def auto_anchored_vwap(highs: np.ndarray, lows: np.ndarray, closes: np.ndarray, volumes: np.ndarray, anchor_index: int = 0) -> np.ndarray:
    """Calculate VWAP Auto Anchored from a specific anchor point."""
    if anchor_index >= len(highs) or len(highs) <= anchor_index:
        return np.array([])

    typical_price = (highs + lows + closes) / 3
    anchored_tp = typical_price[anchor_index:]
    anchored_vol = volumes[anchor_index:]
    vwap = np.cumsum(anchored_tp * anchored_vol) / np.cumsum(anchored_vol)
    result = np.full(len(highs), np.nan)
    result[anchor_index:] = vwap
    return result


def supertrend(highs: np.ndarray, lows: np.ndarray, closes: np.ndarray, period: int = 7, multiplier: float = 3.0) -> Tuple[np.ndarray, np.ndarray]:
    """Calculate Supertrend."""
    atr = average_true_range(highs, lows, closes, period)
    if len(atr) == 0:
        return np.array([]), np.array([])

    hl2 = (highs + lows) / 2
    upperband = hl2 + (multiplier * atr)
    lowerband = hl2 - (multiplier * atr)

    trend = np.zeros(len(closes))
    trend[0] = 1

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


def parabolic_sar(highs: np.ndarray, lows: np.ndarray, acceleration: float = 0.02, max_acceleration: float = 0.2) -> np.ndarray:
    """Calculate Parabolic SAR."""
    if len(highs) < 2:
        return np.array([])

    sar = np.zeros(len(highs))
    sar[0] = lows[0]
    ep = highs[0]
    af = acceleration
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


def ichimoku_cloud(highs: np.ndarray, lows: np.ndarray, closes: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Calculate Ichimoku Cloud components."""
    if len(highs) < 52:
        return np.array([]), np.array([]), np.array([]), np.array([]), np.array([])

    # Tenkan-sen (Conversion Line): (9-period high + 9-period low) / 2
    tenkan_high = pd.Series(highs).rolling(window=9).max()
    tenkan_low = pd.Series(lows).rolling(window=9).min()
    tenkan_sen = (tenkan_high + tenkan_low) / 2

    # Kijun-sen (Base Line): (26-period high + 26-period low) / 2
    kijun_high = pd.Series(highs).rolling(window=26).max()
    kijun_low = pd.Series(lows).rolling(window=26).min()
    kijun_sen = (kijun_high + kijun_low) / 2

    # Senkou Span A (Leading Span A): (Tenkan-sen + Kijun-sen) / 2, plotted 26 periods ahead
    senkou_a = ((tenkan_sen + kijun_sen) / 2).shift(26)

    # Senkou Span B (Leading Span B): (52-period high + 52-period low) / 2, plotted 26 periods ahead
    senkou_high = pd.Series(highs).rolling(window=52).max()
    senkou_low = pd.Series(lows).rolling(window=52).min()
    senkou_b = ((senkou_high + senkou_low) / 2).shift(26)

    # Chikou Span (Lagging Span): Close plotted 26 periods back
    chikou = pd.Series(closes).shift(-26)

    return (tenkan_sen.values[51:], kijun_sen.values[51:],
            senkou_a.values[51:], senkou_b.values[51:], chikou.values[51:])


def zig_zag(highs: np.ndarray, lows: np.ndarray, threshold: float = 0.05) -> List[Tuple[float, int]]:
    """Calculate Zig Zag indicator."""
    if len(highs) < 3:
        return []
    pivots = []
    direction = 0
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


def linear_regression_channel(closes: np.ndarray, period: int, std_dev: float = 2.0) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Calculate Linear Regression Channel."""
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


# Oscillators & Momentum

def relative_strength_index(closes: np.ndarray, period: int = 14) -> np.ndarray:
    """Calculate RSI."""
    if len(closes) < period + 1:
        return np.array([])

    gains = np.where(closes[1:] > closes[:-1], closes[1:] - closes[:-1], 0)
    losses = np.where(closes[1:] < closes[:-1], closes[:-1] - closes[1:], 0)

    avg_gain = pd.Series(gains).rolling(window=period).mean()
    avg_loss = pd.Series(losses).rolling(window=period).mean()

    rs = avg_gain / avg_loss
    rs = rs.replace([np.inf, -np.inf], np.nan).fillna(0)
    rsi = 100 - (100 / (1 + rs))
    return rsi.values[period-1:]


def stochastic_oscillator(highs: np.ndarray, lows: np.ndarray, closes: np.ndarray, k_period: int = 14, d_period: int = 3) -> Tuple[np.ndarray, np.ndarray]:
    """Calculate Stochastic Oscillator."""
    if len(highs) < k_period:
        return np.array([]), np.array([])

    lowest_low = pd.Series(lows).rolling(window=k_period).min()
    highest_high = pd.Series(highs).rolling(window=k_period).max()

    k = 100 * ((closes - lowest_low) / (highest_high - lowest_low))
    d = k.rolling(window=d_period).mean()
    return k.values[k_period-1:], d.values[k_period + d_period - 2:]


def stochastic_rsi(closes: np.ndarray, rsi_period: int = 14, stoch_period: int = 14, k_period: int = 3, d_period: int = 3) -> Tuple[np.ndarray, np.ndarray]:
    """Calculate Stochastic RSI."""
    rsi = relative_strength_index(closes, rsi_period)
    if len(rsi) < stoch_period:
        return np.array([]), np.array([])

    lowest_rsi = pd.Series(rsi).rolling(window=stoch_period).min()
    highest_rsi = pd.Series(rsi).rolling(window=stoch_period).max()
    stoch_rsi_k = 100 * ((rsi - lowest_rsi) / (highest_rsi - lowest_rsi))
    stoch_rsi_d = stoch_rsi_k.rolling(window=d_period).mean()
    return stoch_rsi_k.values[stoch_period-1:], stoch_rsi_d.values[stoch_period + d_period - 2:]


def stochastic_momentum_index(highs: np.ndarray, lows: np.ndarray, closes: np.ndarray, k_period: int = 14, smooth1: int = 3, smooth2: int = 3) -> np.ndarray:
    """Calculate Stochastic Momentum Index."""
    if len(highs) < k_period:
        return np.array([])

    median_price = (highs + lows) / 2
    lowest_low = pd.Series(lows).rolling(window=k_period).min()
    highest_high = pd.Series(highs).rolling(window=k_period).max()
    smi = 100 * ((closes - lowest_low) / (highest_high - lowest_low) - 0.5)
    smi_smooth1 = pd.Series(smi).rolling(window=smooth1).mean()
    smi_smooth2 = smi_smooth1.rolling(window=smooth2).mean()
    return smi_smooth2.values[k_period + smooth1 + smooth2 - 3:]


def macd(closes: np.ndarray, fast_period: int = 12, slow_period: int = 26, signal_period: int = 9) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Calculate MACD."""
    if len(closes) < slow_period + signal_period:
        return np.array([]), np.array([]), np.array([])

    fast_ema = pd.Series(closes).ewm(span=fast_period).mean()
    slow_ema = pd.Series(closes).ewm(span=slow_period).mean()
    macd_line = fast_ema - slow_ema
    signal = macd_line.ewm(span=signal_period).mean()
    histogram = macd_line - signal
    return macd_line.values[slow_period-1:], signal.values[slow_period + signal_period - 2:], histogram.values[slow_period + signal_period - 2:]


def momentum(closes: np.ndarray, period: int) -> np.ndarray:
    """Calculate Momentum."""
    if len(closes) < period + 1:
        return np.array([])
    return closes[period:] - closes[:-period]


def rate_of_change(closes: np.ndarray, period: int) -> np.ndarray:
    """Calculate Rate of Change."""
    if len(closes) < period + 1:
        return np.array([])
    return ((closes[period:] - closes[:-period]) / closes[:-period]) * 100


def williams_percent_r(highs: np.ndarray, lows: np.ndarray, closes: np.ndarray, period: int = 14) -> np.ndarray:
    """Calculate Williams %R."""
    if len(highs) < period:
        return np.array([])

    highest_high = pd.Series(highs).rolling(window=period).max()
    lowest_low = pd.Series(lows).rolling(window=period).min()
    williams_r = -100 * ((highest_high - closes) / (highest_high - lowest_low))
    return williams_r.values[period-1:]


def awesome_oscillator(highs: np.ndarray, lows: np.ndarray, short_period: int = 5, long_period: int = 34) -> np.ndarray:
    """Calculate Awesome Oscillator."""
    median_price = (highs + lows) / 2
    short_sma = pd.Series(median_price).rolling(window=short_period).mean()
    long_sma = pd.Series(median_price).rolling(window=long_period).mean()
    ao = short_sma - long_sma
    return ao.values[long_period-1:]


def ultimate_oscillator(highs: np.ndarray, lows: np.ndarray, closes: np.ndarray, short_period: int = 7, medium_period: int = 14, long_period: int = 28) -> np.ndarray:
    """Calculate Ultimate Oscillator."""
    if len(highs) < long_period:
        return np.array([])

    bp = closes - np.minimum(lows, pd.Series(closes).shift(1))
    tr = np.maximum(highs - lows, np.maximum(np.abs(highs - pd.Series(closes).shift(1)), np.abs(lows - pd.Series(closes).shift(1))))

    avg7 = pd.Series(bp).rolling(window=short_period).sum() / pd.Series(tr).rolling(window=short_period).sum()
    avg14 = pd.Series(bp).rolling(window=medium_period).sum() / pd.Series(tr).rolling(window=medium_period).sum()
    avg28 = pd.Series(bp).rolling(window=long_period).sum() / pd.Series(tr).rolling(window=long_period).sum()

    uo = 100 * (4 * avg7 + 2 * avg14 + avg28) / 7
    return uo.values[long_period-1:]


def detrended_price_oscillator(closes: np.ndarray, period: int = 21) -> np.ndarray:
    """Calculate Detrended Price Oscillator."""
    if len(closes) < period * 2:
        return np.array([])

    sma = pd.Series(closes).rolling(window=period).mean()
    dpo = closes[period:] - sma.values[:-period]
    return dpo


def chaikin_oscillator(highs: np.ndarray, lows: np.ndarray, closes: np.ndarray, volumes: np.ndarray, short_period: int = 3, long_period: int = 10) -> np.ndarray:
    """Calculate Chaikin Oscillator."""
    ad = accumulation_distribution(highs, lows, closes, volumes)
    short_ema = pd.Series(ad).ewm(span=short_period).mean()
    long_ema = pd.Series(ad).ewm(span=long_period).mean()
    return (short_ema - long_ema).values[long_period-1:]


def chande_momentum_oscillator(closes: np.ndarray, period: int = 14) -> np.ndarray:
    """Calculate Chande Momentum Oscillator."""
    if len(closes) < period + 1:
        return np.array([])

    gains = np.where(closes[1:] > closes[:-1], closes[1:] - closes[:-1], 0)
    losses = np.where(closes[1:] < closes[:-1], closes[:-1] - closes[1:], 0)

    sum_gains = pd.Series(gains).rolling(window=period).sum()
    sum_losses = pd.Series(losses).rolling(window=period).sum()

    cmo = 100 * (sum_gains - sum_losses) / (sum_gains + sum_losses)
    return cmo.values[period-1:]


def commodity_channel_index(highs: np.ndarray, lows: np.ndarray, closes: np.ndarray, period: int = 20) -> np.ndarray:
    """Calculate Commodity Channel Index."""
    if len(highs) < period:
        return np.array([])

    typical_price = (highs + lows + closes) / 3
    sma_tp = pd.Series(typical_price).rolling(window=period).mean()
    mad = pd.Series(typical_price).rolling(window=period).apply(lambda x: np.mean(np.abs(x - x.mean())), raw=False)
    cci = (typical_price - sma_tp) / (0.015 * mad)
    return cci.values[period-1:]


def woodies_cci(highs: np.ndarray, lows: np.ndarray, closes: np.ndarray, cci_period: int = 14, smooth_period: int = 2) -> np.ndarray:
    """Calculate Woodies CCI."""
    cci = commodity_channel_index(highs, lows, closes, cci_period)
    if len(cci) < smooth_period:
        return np.array([])
    smoothed_cci = pd.Series(cci).ewm(span=smooth_period).mean()
    return smoothed_cci.values[smooth_period-1:]


def coppock_curve(closes: np.ndarray, short_roc: int = 11, long_roc: int = 14, wma_period: int = 10) -> np.ndarray:
    """Calculate Coppock Curve."""
    if len(closes) < long_roc + wma_period:
        return np.array([])

    roc_short = rate_of_change(closes, short_roc)
    roc_long = rate_of_change(closes, long_roc)
    coppock = roc_short + roc_long

    # WMA of Coppock
    wma = pd.Series(coppock).rolling(window=wma_period).apply(lambda x: np.sum(x * np.arange(1, len(x)+1)) / np.sum(np.arange(1, len(x)+1)), raw=False)
    return wma.values[wma_period-1:]


def know_sure_thing(closes: np.ndarray, r1: int = 10, r2: int = 15, r3: int = 20, r4: int = 30, s1: int = 10, s2: int = 10, s3: int = 10, s4: int = 15) -> np.ndarray:
    """Calculate Know Sure Thing."""
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


def mass_index(highs: np.ndarray, lows: np.ndarray, ema_period: int = 9, sum_period: int = 25) -> np.ndarray:
    """Calculate Mass Index."""
    if len(highs) < ema_period + sum_period:
        return np.array([])

    hl = highs - lows
    ema1 = pd.Series(hl).ewm(span=ema_period).mean()
    ema2 = ema1.ewm(span=ema_period).mean()
    ratio = ema1 / ema2
    mass = ratio.rolling(window=sum_period).sum()
    return mass.values[ema_period + sum_period - 2:]


def relative_vigor_index(highs: np.ndarray, lows: np.ndarray, closes: np.ndarray, opens: np.ndarray, period: int = 10) -> np.ndarray:
    """Calculate Relative Vigor Index."""
    if len(highs) < period:
        return np.array([])

    numerator = (closes - opens) / (highs - lows)
    rvi = pd.Series(numerator).rolling(window=period).mean()
    return rvi.values[period-1:]


def relative_volatility_index(highs: np.ndarray, lows: np.ndarray, period: int = 10) -> np.ndarray:
    """Calculate Relative Volatility Index."""
    volatility = highs - lows
    return relative_strength_index(volatility, period)


def true_strength_index(closes: np.ndarray, short_period: int = 25, long_period: int = 13) -> np.ndarray:
    """Calculate True Strength Index."""
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


def trend_strength_index(highs: np.ndarray, lows: np.ndarray, closes: np.ndarray, period: int = 14) -> np.ndarray:
    """Calculate Trend Strength Index."""
    fast = pd.Series(closes).rolling(window=5).mean()
    slow = pd.Series(closes).rolling(window=10).mean()
    if len(fast) == 0 or len(slow) == 0:
        return np.array([])
    min_len = min(len(fast), len(slow))
    tsi = np.zeros(min_len)
    for i in range(min_len):
        if slow.iloc[i] != 0:
            tsi[i] = (fast.iloc[i] - slow.iloc[i]) / slow.iloc[i] * 100
    return tsi


# Volatility & Bands

def average_true_range(highs: np.ndarray, lows: np.ndarray, closes: np.ndarray, period: int = 14) -> np.ndarray:
    """Calculate Average True Range."""
    if len(highs) < period + 1:
        return np.array([])

    tr = np.maximum(highs[1:] - lows[1:],
                   np.maximum(np.abs(highs[1:] - closes[:-1]),
                             np.abs(lows[1:] - closes[:-1])))

    atr = pd.Series(tr).rolling(window=period).mean()
    return atr.values[period-1:]


def bollinger_bands(closes: np.ndarray, period: int = 20, std_dev: float = 2.0) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Calculate Bollinger Bands."""
    if len(closes) < period:
        return np.array([]), np.array([]), np.array([])

    sma = pd.Series(closes).rolling(window=period).mean()
    std = pd.Series(closes).rolling(window=period).std()
    upper = sma + (std * std_dev)
    lower = sma - (std * std_dev)
    return upper.values[period-1:], sma.values[period-1:], lower.values[period-1:]


def keltner_channels(highs: np.ndarray, lows: np.ndarray, closes: np.ndarray, period: int = 20, multiplier: float = 2.0) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Calculate Keltner Channels."""
    if len(highs) < period:
        return np.array([]), np.array([]), np.array([])

    typical_price = (highs + lows + closes) / 3
    ema = pd.Series(typical_price).ewm(span=period).mean()
    atr = average_true_range(highs, lows, closes, period)

    if len(atr) == 0:
        return np.array([]), np.array([]), np.array([])

    upper = ema + (multiplier * atr)
    lower = ema - (multiplier * atr)
    return upper.values[period-1:], ema.values[period-1:], lower.values[period-1:]


def donchian_channels(highs: np.ndarray, lows: np.ndarray, period: int = 20) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Calculate Donchian Channels."""
    if len(highs) < period:
        return np.array([]), np.array([]), np.array([])

    upper = pd.Series(highs).rolling(window=period).max()
    lower = pd.Series(lows).rolling(window=period).min()
    middle = (upper + lower) / 2
    return upper.values[period-1:], middle.values[period-1:], lower.values[period-1:]


def stochastics_bands(highs: np.ndarray, lows: np.ndarray, closes: np.ndarray, period: int = 20, std_dev: float = 2.0) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Calculate Stochastics Bands."""
    k, d = stochastic_oscillator(highs, lows, closes, period)
    if len(k) == 0:
        return np.array([]), np.array([]), np.array([])

    k_series = pd.Series(k)
    upper = k_series.rolling(window=period).mean() + (k_series.rolling(window=period).std() * std_dev)
    lower = k_series.rolling(window=period).mean() - (k_series.rolling(window=period).std() * std_dev)
    middle = k_series.rolling(window=period).mean()
    return upper.values[period-1:], middle.values[period-1:], lower.values[period-1:]


def price_channel(highs: np.ndarray, lows: np.ndarray, period: int = 20) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Calculate Price Channel."""
    return donchian_channels(highs, lows, period)


def envelope(closes: np.ndarray, period: int = 20, percentage: float = 2.5) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Calculate Envelope."""
    if len(closes) < period:
        return np.array([]), np.array([]), np.array([])

    sma = pd.Series(closes).rolling(window=period).mean()
    upper = sma * (1 + percentage / 100)
    lower = sma * (1 - percentage / 100)
    return upper.values[period-1:], sma.values[period-1:], lower.values[period-1:]


def fractal_dimension(highs: np.ndarray, lows: np.ndarray, period: int = 10) -> np.ndarray:
    """Calculate Fractal Dimension."""
    if len(highs) < period:
        return np.array([])

    result = np.zeros(len(highs) - period + 1)
    for i in range(period, len(highs) + 1):
        h_window = highs[i-period:i]
        l_window = lows[i-period:i]

        # Calculate fractal dimension using Higuchi method (simplified)
        n = len(h_window)
        max_h = np.max(h_window)
        min_h = np.min(h_window)
        max_l = np.max(l_window)
        min_l = np.min(l_window)

        range_h = max_h - min_h
        range_l = max_l - min_l

        if range_h == 0 or range_l == 0:
            fd = 1.0
        else:
            # Simplified fractal dimension calculation
            fd = 1 + np.log(range_h + range_l) / np.log(n)

        result[i - period] = fd

    return result


def chaikin_volatility(highs: np.ndarray, lows: np.ndarray, period: int = 10, roc_period: int = 12) -> np.ndarray:
    """Calculate Chaikin Volatility."""
    if len(highs) < period + roc_period:
        return np.array([])

    hl_range = highs - lows
    ema = pd.Series(hl_range).ewm(span=period).mean()
    chaikin_vol = (ema - ema.shift(roc_period)) / ema.shift(roc_period) * 100
    return chaikin_vol.values[period + roc_period - 2:]


def historical_volatility(closes: np.ndarray, period: int = 21) -> np.ndarray:
    """Calculate Historical Volatility."""
    if len(closes) < period + 1:
        return np.array([])

    returns = np.log(closes[1:] / closes[:-1])
    vol = pd.Series(returns).rolling(window=period).std() * np.sqrt(252)  # Annualized
    return vol.values[period-1:]


def normalized_average_true_range(highs: np.ndarray, lows: np.ndarray, closes: np.ndarray, period: int = 14) -> np.ndarray:
    """Calculate Normalized ATR."""
    atr = average_true_range(highs, lows, closes, period)
    if len(atr) == 0:
        return np.array([])

    closes_subset = closes[period-1:]
    natr = (atr / closes_subset) * 100
    return natr


def true_range(highs: np.ndarray, lows: np.ndarray, closes: np.ndarray) -> np.ndarray:
    """Calculate True Range."""
    if len(highs) < 2:
        return np.array([])

    tr = np.maximum(highs[1:] - lows[1:],
                   np.maximum(np.abs(highs[1:] - closes[:-1]),
                             np.abs(lows[1:] - closes[:-1])))
    return tr


def standard_deviation(closes: np.ndarray, period: int = 20) -> np.ndarray:
    """Calculate Standard Deviation."""
    if len(closes) < period:
        return np.array([])
    return pd.Series(closes).rolling(window=period).std().values[period-1:]


def variance(closes: np.ndarray, period: int = 20) -> np.ndarray:
    """Calculate Variance."""
    if len(closes) < period:
        return np.array([])
    return pd.Series(closes).rolling(window=period).var().values[period-1:]


def coefficient_of_variation(closes: np.ndarray, period: int = 20) -> np.ndarray:
    """Calculate Coefficient of Variation."""
    if len(closes) < period:
        return np.array([])

    mean = pd.Series(closes).rolling(window=period).mean()
    std = pd.Series(closes).rolling(window=period).std()
    cv = std / mean
    return cv.values[period-1:]


# Specialized / Proprietary

def vortex_indicator(highs: np.ndarray, lows: np.ndarray, closes: np.ndarray, period: int = 14) -> Tuple[np.ndarray, np.ndarray]:
    """Calculate Vortex Indicator."""
    if len(highs) < period + 1:
        return np.array([]), np.array([])

    vm_plus = np.abs(highs[1:] - lows[:-1])
    vm_minus = np.abs(lows[1:] - highs[:-1])

    sum_plus = pd.Series(vm_plus).rolling(window=period).sum()
    sum_minus = pd.Series(vm_minus).rolling(window=period).sum()
    tr_sum = pd.Series(true_range(highs, lows, closes)).rolling(window=period).sum()

    vi_plus = sum_plus / tr_sum
    vi_minus = sum_minus / tr_sum

    return vi_plus.values[period-1:], vi_minus.values[period-1:]


def elder_ray_index(highs: np.ndarray, lows: np.ndarray, closes: np.ndarray, period: int = 13) -> Tuple[np.ndarray, np.ndarray]:
    """Calculate Elder Ray Index (Bull Power and Bear Power)."""
    if len(highs) < period:
        return np.array([]), np.array([])

    ema = pd.Series(closes).ewm(span=period).mean()
    bull_power = highs - ema
    bear_power = lows - ema
    return bull_power.values[period-1:], bear_power.values[period-1:]


def balance_of_power(highs: np.ndarray, lows: np.ndarray, opens: np.ndarray, closes: np.ndarray) -> np.ndarray:
    """Calculate Balance of Power."""
    return (closes - opens) / (highs - lows)


def market_facilitation_index(highs: np.ndarray, lows: np.ndarray, volumes: np.ndarray) -> np.ndarray:
    """Calculate Market Facilitation Index."""
    return (highs - lows) / volumes


def schaff_trend_cycle(closes: np.ndarray, cycle: int = 10, short_cycle: int = 23, long_cycle: int = 50) -> np.ndarray:
    """Calculate Schaff Trend Cycle."""
    if len(closes) < long_cycle:
        return np.array([])

    # Calculate MACD
    macd_line, _, _ = macd(closes, short_cycle, long_cycle, cycle)
    if len(macd_line) == 0:
        return np.array([])

    # Cycle MACD
    cycle_macd = pd.Series(macd_line).ewm(span=cycle).mean()

    # Smooth cycle MACD
    smooth1 = cycle_macd.ewm(span=cycle).mean()
    smooth2 = smooth1.ewm(span=cycle).mean()

    # Calculate STC
    stc = np.zeros(len(smooth2))
    for i in range(len(stc)):
        if smooth2.iloc[i] != smooth1.iloc[i]:
            stc[i] = (smooth2.iloc[i] - smooth1.iloc[i]) / abs(smooth2.iloc[i] - smooth1.iloc[i]) * 100
        else:
            stc[i] = 50

    return stc


def rainbow_oscillator(closes: np.ndarray, periods: List[int] = None) -> Dict[int, np.ndarray]:
    """Calculate Rainbow Oscillator."""
    if periods is None:
        periods = [2, 3, 4, 5, 6, 7, 8, 9, 10]

    rainbow = {}
    for period in periods:
        rainbow[period] = pd.Series(closes).ewm(span=period).mean().values[period-1:]

    return rainbow


def rainbow_charts(highs: np.ndarray, lows: np.ndarray, closes: np.ndarray, periods: List[int] = None) -> Dict[str, Dict[int, np.ndarray]]:
    """Calculate Rainbow Charts (SMA and EMA versions)."""
    if periods is None:
        periods = [3, 5, 8, 10, 12, 15, 30, 35, 40, 45, 50, 60]

    rainbow_sma = {}
    rainbow_ema = {}

    for period in periods:
        rainbow_sma[period] = pd.Series(closes).rolling(window=period).mean().values[period-1:]
        rainbow_ema[period] = pd.Series(closes).ewm(span=period).mean().values[period-1:]

    return {'SMA': rainbow_sma, 'EMA': rainbow_ema}


def guppy_multiple_moving_average(closes: np.ndarray) -> Dict[str, Dict[int, np.ndarray]]:
    """Calculate Guppy Multiple Moving Average."""
    short_periods = [3, 5, 8, 10, 12, 15]
    long_periods = [30, 35, 40, 45, 50, 60]

    gmma = {'short': {}, 'long': {}}

    for period in short_periods:
        gmma['short'][period] = pd.Series(closes).ewm(span=period).mean().values[period-1:]

    for period in long_periods:
        gmma['long'][period] = pd.Series(closes).ewm(span=period).mean().values[period-1:]

    return gmma


def heikin_ashi(highs: np.ndarray, lows: np.ndarray, opens: np.ndarray, closes: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Calculate Heikin-Ashi candles."""
    ha_close = (opens + highs + lows + closes) / 4
    ha_open = np.zeros(len(closes))
    ha_open[0] = (opens[0] + closes[0]) / 2

    for i in range(1, len(closes)):
        ha_open[i] = (ha_open[i-1] + ha_close[i-1]) / 2

    ha_high = np.maximum(np.maximum(highs, ha_open), ha_close)
    ha_low = np.minimum(np.minimum(lows, ha_open), ha_close)

    return ha_open, ha_high, ha_low, ha_close


def renko_bricks(closes: np.ndarray, brick_size: float) -> List[Dict]:
    """Calculate Renko bricks."""
    bricks = []
    current_price = closes[0]
    direction = 0  # 0: neutral, 1: up, -1: down

    for price in closes[1:]:
        price_diff = price - current_price

        if abs(price_diff) >= brick_size:
            num_bricks = int(abs(price_diff) // brick_size)
            brick_direction = 1 if price_diff > 0 else -1

            for _ in range(num_bricks):
                bricks.append({
                    'direction': brick_direction,
                    'price': current_price + (brick_direction * brick_size),
                    'size': brick_size
                })
                current_price += brick_direction * brick_size

            # Handle remainder
            remainder = abs(price_diff) % brick_size
            if remainder > 0:
                current_price += brick_direction * remainder

    return bricks


def point_and_figure(highs: np.ndarray, lows: np.ndarray, box_size: float, reversal: int = 3) -> List[Dict]:
    """Calculate Point and Figure chart."""
    columns = []
    current_column = {'type': 'X', 'boxes': []}
    current_price = (highs[0] + lows[0]) / 2
    current_high = current_price
    current_low = current_price

    for h, l in zip(highs[1:], lows[1:]):
        price_range = (h + l) / 2

        if current_column['type'] == 'X':  # Uptrend
            if price_range >= current_high + box_size:
                # Add X boxes
                num_boxes = int((price_range - current_high) // box_size)
                for _ in range(num_boxes):
                    current_column['boxes'].append(current_high + box_size)
                    current_high += box_size
            elif price_range <= current_low - (box_size * reversal):
                # Reversal to O
                columns.append(current_column)
                current_column = {'type': 'O', 'boxes': []}
                current_low = current_high - box_size
                current_high = current_high

        else:  # Downtrend (O)
            if price_range <= current_low - box_size:
                # Add O boxes
                num_boxes = int((current_low - price_range) // box_size)
                for _ in range(num_boxes):
                    current_column['boxes'].append(current_low - box_size)
                    current_low -= box_size
            elif price_range >= current_high + (box_size * reversal):
                # Reversal to X
                columns.append(current_column)
                current_column = {'type': 'X', 'boxes': []}
                current_high = current_low + box_size
                current_low = current_low

    if current_column['boxes']:
        columns.append(current_column)

    return columns


def kagi_chart(highs: np.ndarray, lows: np.ndarray, reversal_threshold: float) -> List[Dict]:
    """Calculate Kagi chart."""
    kagi_lines = []
    current_direction = 0  # 0: neutral, 1: up (yang), -1: down (yin)
    current_price = (highs[0] + lows[0]) / 2
    line_start = current_price

    for h, l in zip(highs[1:], lows[1:]):
        price = (h + l) / 2

        if current_direction == 0:
            if price >= current_price + reversal_threshold:
                current_direction = 1
                kagi_lines.append({'direction': 1, 'start': line_start, 'end': price})
                line_start = price
            elif price <= current_price - reversal_threshold:
                current_direction = -1
                kagi_lines.append({'direction': -1, 'start': line_start, 'end': price})
                line_start = price

        elif current_direction == 1:  # Yang line
            if price > current_price:
                current_price = price
            elif price <= current_price - reversal_threshold:
                kagi_lines.append({'direction': -1, 'start': line_start, 'end': price})
                current_direction = -1
                current_price = price
                line_start = price

        else:  # Yin line
            if price < current_price:
                current_price = price
            elif price >= current_price + reversal_threshold:
                kagi_lines.append({'direction': 1, 'start': line_start, 'end': price})
                current_direction = 1
                current_price = price
                line_start = price

    return kagi_lines


def three_line_break(highs: np.ndarray, lows: np.ndarray, closes: np.ndarray) -> List[Dict]:
    """Calculate Three Line Break chart."""
    breaks = []
    current_direction = 0  # 0: neutral, 1: up, -1: down
    pivot_high = highs[0]
    pivot_low = lows[0]

    for h, l, c in zip(highs[1:], lows[1:], closes[1:]):
        if current_direction >= 0:  # Uptrend or neutral
            if c > pivot_high:
                breaks.append({'direction': 1, 'high': c, 'low': pivot_high})
                pivot_high = c
                current_direction = min(current_direction + 1, 3)
            elif current_direction == 3 and c < pivot_low:
                # Reversal
                breaks.append({'direction': -1, 'high': pivot_low, 'low': c})
                pivot_low = c
                current_direction = -1
            else:
                current_direction = 0

        else:  # Downtrend
            if c < pivot_low:
                breaks.append({'direction': -1, 'high': pivot_low, 'low': c})
                pivot_low = c
                current_direction = max(current_direction - 1, -3)
            elif current_direction == -3 and c > pivot_high:
                # Reversal
                breaks.append({'direction': 1, 'high': c, 'low': pivot_high})
                pivot_high = c
                current_direction = 1
            else:
                current_direction = 0

    return breaks
