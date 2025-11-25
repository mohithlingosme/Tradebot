"""
Stochastic Oscillator Indicator

The Stochastic Oscillator is a momentum indicator that compares a particular closing price
of a security to a range of its prices over a certain period of time.
"""

import numpy as np
from typing import List, Optional, Dict


class StochasticOscillator:
    """
    Stochastic Oscillator indicator.

    Components:
    - %K Line: Current close relative to period's price range
    - %D Line: Simple moving average of %K
    """

    def __init__(self, k_period: int = 14, d_period: int = 3):
        """
        Initialize Stochastic Oscillator.

        Args:
            k_period: Lookback period for %K calculation (default: 14)
            d_period: Period for %D moving average (default: 3)
        """
        self.k_period = k_period
        self.d_period = d_period

    def calculate(self, highs: List[float], lows: List[float], closes: List[float]) -> Optional[Dict[str, float]]:
        """
        Calculate Stochastic Oscillator for the given price series.

        Args:
            highs: List of high prices
            lows: List of low prices
            closes: List of closing prices

        Returns:
            Dictionary with %K and %D values or None if insufficient data
        """
        if len(highs) < self.k_period or len(lows) < self.k_period or len(closes) < self.k_period:
            return None

        # Calculate %K
        highest_high = max(highs[-self.k_period:])
        lowest_low = min(lows[-self.k_period:])
        current_close = closes[-1]

        if highest_high == lowest_low:
            k_value = 50.0  # Neutral when no range
        else:
            k_value = ((current_close - lowest_low) / (highest_high - lowest_low)) * 100

        # Calculate %D (SMA of %K values)
        k_values = []
        for i in range(self.k_period, len(closes) + 1):
            hh = max(highs[i-self.k_period:i])
            ll = min(lows[i-self.k_period:i])
            cc = closes[i-1]
            if hh == ll:
                k = 50.0
            else:
                k = ((cc - ll) / (hh - ll)) * 100
            k_values.append(k)

        if len(k_values) < self.d_period:
            d_value = k_value
        else:
            d_value = np.mean(k_values[-self.d_period:])

        return {
            'k_percent': k_value,
            'd_percent': d_value
        }

    def calculate_series(self, highs: List[float], lows: List[float], closes: List[float]) -> List[Optional[Dict[str, float]]]:
        """
        Calculate Stochastic Oscillator for each point in the price series.

        Args:
            highs: List of high prices
            lows: List of low prices
            closes: List of closing prices

        Returns:
            List of Stochastic dictionaries
        """
        stoch_values = []
        for i in range(len(closes)):
            if i < self.k_period - 1:
                stoch_values.append(None)
            else:
                stoch = self.calculate(highs[:i+1], lows[:i+1], closes[:i+1])
                stoch_values.append(stoch)
        return stoch_values

    @staticmethod
    def get_signal(stoch_data: Dict[str, float], overbought: float = 80, oversold: float = 20) -> str:
        """
        Get trading signal based on Stochastic Oscillator.

        Args:
            stoch_data: Stochastic calculation result
            overbought: Overbought threshold (default: 80)
            oversold: Oversold threshold (default: 20)

        Returns:
            Signal: 'overbought', 'oversold', 'bullish_crossover', 'bearish_crossover', or 'neutral'
        """
        k = stoch_data['k_percent']
        d = stoch_data['d_percent']

        if k >= overbought and d >= overbought:
            return 'overbought'
        elif k <= oversold and d <= oversold:
            return 'oversold'
        elif k > d:
            return 'bullish_crossover'
        elif k < d:
            return 'bearish_crossover'
        else:
            return 'neutral'
