"""
Commodity Channel Index (CCI) Indicator

CCI measures the difference between a security's price change and its average price change.
High values indicate the price is well above its average, low values indicate well below.
"""

import numpy as np
from typing import List, Optional


class CCI:
    """
    Commodity Channel Index (CCI) indicator.

    Formula:
    CCI = (Typical Price - SMA of Typical Price) / (0.015 × Mean Deviation)
    Typical Price = (High + Low + Close) / 3
    """

    def __init__(self, period: int = 20):
        """
        Initialize CCI indicator.

        Args:
            period: Lookback period (default: 20)
        """
        self.period = period

    def calculate(self, highs: List[float], lows: List[float], closes: List[float]) -> Optional[float]:
        """
        Calculate CCI for the given price series.

        Args:
            highs: List of high prices
            lows: List of low prices
            closes: List of closing prices

        Returns:
            CCI value or None if insufficient data
        """
        if len(highs) < self.period or len(lows) < self.period or len(closes) < self.period:
            return None

        # Calculate Typical Price
        typical_prices = [(h + l + c) / 3 for h, l, c in zip(highs[-self.period:], lows[-self.period:], closes[-self.period:])]

        # Calculate SMA of Typical Price
        sma_tp = np.mean(typical_prices)

        # Calculate Mean Deviation
        mean_deviation = np.mean([abs(tp - sma_tp) for tp in typical_prices])

        if mean_deviation == 0:
            return 0.0

        # Calculate CCI
        current_tp = (highs[-1] + lows[-1] + closes[-1]) / 3
        cci = (current_tp - sma_tp) / (0.015 * mean_deviation)

        return cci

    def calculate_series(self, highs: List[float], lows: List[float], closes: List[float]) -> List[Optional[float]]:
        """
        Calculate CCI for each point in the price series.

        Args:
            highs: List of high prices
            lows: List of low prices
            closes: List of closing prices

        Returns:
            List of CCI values
        """
        cci_values = []
        for i in range(len(closes)):
            if i < self.period - 1:
                cci_values.append(None)
            else:
                cci = self.calculate(highs[:i+1], lows[:i+1], closes[:i+1])
                cci_values.append(cci)
        return cci_values

    @staticmethod
    def get_signal(cci_value: float, overbought: float = 100, oversold: float = -100) -> str:
        """
        Get trading signal based on CCI value.

        Args:
            cci_value: Current CCI value
            overbought: Overbought threshold (default: 100)
            oversold: Oversold threshold (default: -100)

        Returns:
            Signal: 'overbought', 'oversold', or 'neutral'
        """
        if cci_value >= overbought:
            return 'overbought'
        elif cci_value <= oversold:
            return 'oversold'
        else:
            return 'neutral'
