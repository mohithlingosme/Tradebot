"""
Relative Strength Index (RSI) Indicator

The RSI is a momentum oscillator that measures the speed and change of price movements.
It oscillates between 0 and 100, typically using a 14-day period.
"""

import numpy as np
from typing import List, Optional


class RSI:
    """
    Relative Strength Index (RSI) indicator.

    Formula:
    RSI = 100 - (100 / (1 + RS))
    RS = Average Gain / Average Loss
    """

    def __init__(self, period: int = 14):
        """
        Initialize RSI indicator.

        Args:
            period: Lookback period for RSI calculation (default: 14)
        """
        self.period = period
        self.gains = []
        self.losses = []

    def calculate(self, prices: List[float]) -> Optional[float]:
        """
        Calculate RSI for the given price series.

        Args:
            prices: List of closing prices

        Returns:
            RSI value (0-100) or None if insufficient data
        """
        if len(prices) < self.period + 1:
            return None

        # Calculate price changes
        deltas = np.diff(prices)

        # Separate gains and losses
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)

        # Calculate average gains and losses
        avg_gain = np.mean(gains[-self.period:])
        avg_loss = np.mean(losses[-self.period:])

        if avg_loss == 0:
            return 100.0

        # Calculate RS and RSI
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))

        return rsi

    def calculate_series(self, prices: List[float]) -> List[Optional[float]]:
        """
        Calculate RSI for each point in the price series.

        Args:
            prices: List of closing prices

        Returns:
            List of RSI values
        """
        rsi_values = []
        for i in range(len(prices)):
            if i < self.period:
                rsi_values.append(None)
            else:
                rsi = self.calculate(prices[:i+1])
                rsi_values.append(rsi)
        return rsi_values

    @staticmethod
    def get_signal(rsi_value: float, overbought: float = 70, oversold: float = 30) -> str:
        """
        Get trading signal based on RSI value.

        Args:
            rsi_value: Current RSI value
            overbought: Overbought threshold (default: 70)
            oversold: Oversold threshold (default: 30)

        Returns:
            Signal: 'overbought', 'oversold', or 'neutral'
        """
        if rsi_value >= overbought:
            return 'overbought'
        elif rsi_value <= oversold:
            return 'oversold'
        else:
            return 'neutral'
