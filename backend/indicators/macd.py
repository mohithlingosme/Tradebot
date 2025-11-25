"""
Moving Average Convergence Divergence (MACD) Indicator

MACD is a trend-following momentum indicator that shows the relationship between
two moving averages of a security's price.
"""

import numpy as np
from typing import List, Optional, Dict, Tuple


class MACD:
    """
    Moving Average Convergence Divergence (MACD) indicator.

    Components:
    - MACD Line: (12-period EMA - 26-period EMA)
    - Signal Line: 9-period EMA of MACD Line
    - Histogram: MACD Line - Signal Line
    """

    def __init__(self, fast_period: int = 12, slow_period: int = 26, signal_period: int = 9):
        """
        Initialize MACD indicator.

        Args:
            fast_period: Fast EMA period (default: 12)
            slow_period: Slow EMA period (default: 26)
            signal_period: Signal line EMA period (default: 9)
        """
        self.fast_period = fast_period
        self.slow_period = slow_period
        self.signal_period = signal_period

    def calculate(self, prices: List[float]) -> Optional[Dict[str, float]]:
        """
        Calculate MACD for the given price series.

        Args:
            prices: List of closing prices

        Returns:
            Dictionary with MACD components or None if insufficient data
        """
        if len(prices) < self.slow_period + self.signal_period:
            return None

        # Calculate EMAs
        fast_ema = self._calculate_ema(prices, self.fast_period)
        slow_ema = self._calculate_ema(prices, self.slow_period)

        # Calculate MACD line
        macd_line = fast_ema - slow_ema

        # Calculate signal line (EMA of MACD line)
        macd_values = []
        for i in range(len(prices)):
            if i >= self.slow_period - 1:
                fast_ema_val = self._calculate_ema(prices[:i+1], self.fast_period)
                slow_ema_val = self._calculate_ema(prices[:i+1], self.slow_period)
                macd_values.append(fast_ema_val - slow_ema_val)

        if len(macd_values) < self.signal_period:
            return None

        signal_line = self._calculate_ema(macd_values, self.signal_period)

        # Calculate histogram
        histogram = macd_line - signal_line

        return {
            'macd_line': macd_line,
            'signal_line': signal_line,
            'histogram': histogram
        }

    def calculate_series(self, prices: List[float]) -> List[Optional[Dict[str, float]]]:
        """
        Calculate MACD for each point in the price series.

        Args:
            prices: List of closing prices

        Returns:
            List of MACD dictionaries
        """
        macd_values = []
        for i in range(len(prices)):
            macd = self.calculate(prices[:i+1])
            macd_values.append(macd)
        return macd_values

    def _calculate_ema(self, data: List[float], period: int) -> float:
        """
        Calculate Exponential Moving Average.

        Args:
            data: Price data
            period: EMA period

        Returns:
            EMA value
        """
        if len(data) < period:
            return np.mean(data)

        multiplier = 2 / (period + 1)
        ema = data[0]

        for price in data[1:]:
            ema = (price * multiplier) + (ema * (1 - multiplier))

        return ema

    @staticmethod
    def get_signal(macd_data: Dict[str, float]) -> str:
        """
        Get trading signal based on MACD crossover.

        Args:
            macd_data: MACD calculation result

        Returns:
            Signal: 'bullish_crossover', 'bearish_crossover', or 'neutral'
        """
        macd_line = macd_data['macd_line']
        signal_line = macd_data['signal_line']

        if macd_line > signal_line:
            return 'bullish_crossover'
        elif macd_line < signal_line:
            return 'bearish_crossover'
        else:
            return 'neutral'
