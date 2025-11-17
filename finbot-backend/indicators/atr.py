"""
Average True Range (ATR) Indicator

ATR measures volatility by calculating the average of true ranges over a specified period.
True Range is the maximum of:
1. Current High - Current Low
2. |Current High - Previous Close|
3. |Current Low - Previous Close|
"""

import numpy as np
from typing import List, Optional


class ATR:
    """
    Average True Range (ATR) indicator.

    Formula: ATR = SMA of True Ranges over specified period
    """

    def __init__(self, period: int = 14):
        """
        Initialize ATR indicator.

        Args:
            period: Lookback period (default: 14)
        """
        self.period = period

    def calculate(self, highs: List[float], lows: List[float], closes: List[float]) -> Optional[float]:
        """
        Calculate ATR for the given price series.

        Args:
            highs: List of high prices
            lows: List of low prices
            closes: List of closing prices

        Returns:
            ATR value or None if insufficient data
        """
        if len(highs) < self.period + 1 or len(lows) < self.period + 1 or len(closes) < self.period + 1:
            return None

        # Calculate True Ranges
        true_ranges = []
        for i in range(1, len(highs)):
            tr = max(
                highs[i] - lows[i],  # Current high - current low
                abs(highs[i] - closes[i-1]),  # Current high - previous close
                abs(lows[i] - closes[i-1])   # Current low - previous close
            )
            true_ranges.append(tr)

        if len(true_ranges) < self.period:
            return None

        # Calculate ATR as simple moving average of true ranges
        atr = np.mean(true_ranges[-self.period:])

        return atr

    def calculate_series(self, highs: List[float], lows: List[float], closes: List[float]) -> List[Optional[float]]:
        """
        Calculate ATR for each point in the price series.

        Args:
            highs: List of high prices
            lows: List of low prices
            closes: List of closing prices

        Returns:
            List of ATR values
        """
        atr_values = []
        for i in range(len(closes)):
            if i < self.period:
                atr_values.append(None)
            else:
                atr = self.calculate(highs[:i+1], lows[:i+1], closes[:i+1])
                atr_values.append(atr)
        return atr_values

    @staticmethod
    def get_volatility_level(atr_value: float, average_price: float, high_vol_threshold: float = 0.02) -> str:
        """
        Get volatility level based on ATR relative to price.

        Args:
            atr_value: Current ATR value
            average_price: Average price for comparison
            high_vol_threshold: High volatility threshold as fraction (default: 0.02)

        Returns:
            Volatility level: 'high', 'moderate', or 'low'
        """
        if average_price == 0:
            return 'low'

        volatility_ratio = atr_value / average_price

        if volatility_ratio >= high_vol_threshold:
            return 'high'
        elif volatility_ratio >= high_vol_threshold * 0.5:
            return 'moderate'
        else:
            return 'low'
