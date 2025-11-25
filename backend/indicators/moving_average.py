"""
Moving Average Indicators

This module contains Simple Moving Average (SMA) and Exponential Moving Average (EMA) implementations.
"""

import numpy as np
from typing import List, Optional


class SMA:
    """
    Simple Moving Average (SMA) indicator.

    Formula: SMA = (Sum of prices over period) / period
    """

    def __init__(self, period: int = 20):
        """
        Initialize SMA indicator.

        Args:
            period: Moving average period (default: 20)
        """
        self.period = period

    def calculate(self, prices: List[float]) -> Optional[float]:
        """
        Calculate SMA for the given price series.

        Args:
            prices: List of closing prices

        Returns:
            SMA value or None if insufficient data
        """
        if len(prices) < self.period:
            return None

        return np.mean(prices[-self.period:])

    def calculate_series(self, prices: List[float]) -> List[Optional[float]]:
        """
        Calculate SMA for each point in the price series.

        Args:
            prices: List of closing prices

        Returns:
            List of SMA values
        """
        sma_values = []
        for i in range(len(prices)):
            if i < self.period - 1:
                sma_values.append(None)
            else:
                sma = self.calculate(prices[:i+1])
                sma_values.append(sma)
        return sma_values


class EMA:
    """
    Exponential Moving Average (EMA) indicator.

    Formula: EMA = (Price × Multiplier) + (Previous EMA × (1 - Multiplier))
    Multiplier = 2 / (period + 1)
    """

    def __init__(self, period: int = 20):
        """
        Initialize EMA indicator.

        Args:
            period: Moving average period (default: 20)
        """
        self.period = period

    def calculate(self, prices: List[float]) -> Optional[float]:
        """
        Calculate EMA for the given price series.

        Args:
            prices: List of closing prices

        Returns:
            EMA value or None if insufficient data
        """
        if len(prices) < self.period:
            return None

        multiplier = 2 / (self.period + 1)
        ema = prices[0]

        for price in prices[1:]:
            ema = (price * multiplier) + (ema * (1 - multiplier))

        return ema

    def calculate_series(self, prices: List[float]) -> List[Optional[float]]:
        """
        Calculate EMA for each point in the price series.

        Args:
            prices: List of closing prices

        Returns:
            List of EMA values
        """
        ema_values = []
        for i in range(len(prices)):
            if i < self.period - 1:
                ema_values.append(None)
            else:
                ema = self.calculate(prices[:i+1])
                ema_values.append(ema)
        return ema_values
