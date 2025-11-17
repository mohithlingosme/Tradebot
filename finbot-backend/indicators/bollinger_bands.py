"""
Bollinger Bands Indicator

Bollinger Bands are volatility bands placed above and below a moving average.
The bands widen during periods of high volatility and narrow during periods of low volatility.
"""

import numpy as np
from typing import List, Optional, Dict


class BollingerBands:
    """
    Bollinger Bands indicator.

    Components:
    - Upper Band: SMA + (Standard Deviation × Multiplier)
    - Middle Band: Simple Moving Average (SMA)
    - Lower Band: SMA - (Standard Deviation × Multiplier)
    """

    def __init__(self, period: int = 20, std_dev_multiplier: float = 2.0):
        """
        Initialize Bollinger Bands indicator.

        Args:
            period: Moving average period (default: 20)
            std_dev_multiplier: Standard deviation multiplier (default: 2.0)
        """
        self.period = period
        self.std_dev_multiplier = std_dev_multiplier

    def calculate(self, prices: List[float]) -> Optional[Dict[str, float]]:
        """
        Calculate Bollinger Bands for the given price series.

        Args:
            prices: List of closing prices

        Returns:
            Dictionary with band values or None if insufficient data
        """
        if len(prices) < self.period:
            return None

        # Calculate SMA (middle band)
        sma = np.mean(prices[-self.period:])

        # Calculate standard deviation
        std_dev = np.std(prices[-self.period:])

        # Calculate bands
        upper_band = sma + (std_dev * self.std_dev_multiplier)
        lower_band = sma - (std_dev * self.std_dev_multiplier)

        return {
            'upper_band': upper_band,
            'middle_band': sma,
            'lower_band': lower_band,
            'bandwidth': (upper_band - lower_band) / sma if sma != 0 else 0,
            'percent_b': (prices[-1] - lower_band) / (upper_band - lower_band) if upper_band != lower_band else 0.5
        }

    def calculate_series(self, prices: List[float]) -> List[Optional[Dict[str, float]]]:
        """
        Calculate Bollinger Bands for each point in the price series.

        Args:
            prices: List of closing prices

        Returns:
            List of Bollinger Bands dictionaries
        """
        bands_values = []
        for i in range(len(prices)):
            if i < self.period - 1:
                bands_values.append(None)
            else:
                bands = self.calculate(prices[:i+1])
                bands_values.append(bands)
        return bands_values

    @staticmethod
    def get_signal(bands_data: Dict[str, float], current_price: float) -> str:
        """
        Get trading signal based on Bollinger Bands.

        Args:
            bands_data: Bollinger Bands calculation result
            current_price: Current price

        Returns:
            Signal: 'upper_breakout', 'lower_breakout', 'squeeze', or 'neutral'
        """
        upper = bands_data['upper_band']
        lower = bands_data['lower_band']
        middle = bands_data['middle_band']
        bandwidth = bands_data['bandwidth']

        # Check for breakouts
        if current_price > upper:
            return 'upper_breakout'
        elif current_price < lower:
            return 'lower_breakout'
        elif bandwidth < 0.1:  # Squeeze condition
            return 'squeeze'
        else:
            return 'neutral'
