"""
Arnaud Legoux Moving Average (ALMA) Indicator

The Arnaud Legoux Moving Average is a Gaussian weighted moving average designed to reduce lag and noise.
"""

import numpy as np
from typing import List, Optional


class ArnaudLegouxMovingAverage:
    """
    Arnaud Legoux Moving Average (ALMA) indicator.

    Formula:
    ALMA = sum(w[i] * price[i]) / sum(w[i])
    where w[i] = exp(-((i - m)^2) / (2 * sigma^2))
    m = offset * (window - 1)
    sigma = window / sigma_factor
    """

    def __init__(self, window: int = 9, offset: float = 0.85, sigma_factor: float = 6.0):
        """
        Initialize ALMA indicator.

        Args:
            window: Lookback period (default: 9)
            offset: Offset factor (default: 0.85)
            sigma_factor: Sigma factor (default: 6.0)
        """
        self.window = window
        self.offset = offset
        self.sigma_factor = sigma_factor

    def calculate(self, prices: List[float]) -> Optional[float]:
        """
        Calculate ALMA for the given price series.

        Args:
            prices: List of prices

        Returns:
            ALMA value or None if insufficient data
        """
        if len(prices) < self.window:
            return None

        # Calculate weights
        m = self.offset * (self.window - 1)
        sigma = self.window / self.sigma_factor
        weights = []
        for i in range(self.window):
            w = np.exp(-((i - m) ** 2) / (2 * sigma ** 2))
            weights.append(w)

        # Normalize weights
        weights = np.array(weights)
        weights /= np.sum(weights)

        # Calculate ALMA
        recent_prices = prices[-self.window:]
        alma = np.dot(weights, recent_prices)

        return alma

    def calculate_series(self, prices: List[float]) -> List[Optional[float]]:
        """
        Calculate ALMA for each point in the price series.

        Args:
            prices: List of prices

        Returns:
            List of ALMA values
        """
        alma_values = []
        for i in range(len(prices)):
            if i < self.window - 1:
                alma_values.append(None)
            else:
                alma = self.calculate(prices[:i+1])
                alma_values.append(alma)
        return alma_values
