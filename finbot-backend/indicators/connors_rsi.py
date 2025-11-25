"""
Connors RSI Indicator

The Connors RSI combines RSI, UpDown Length, and Rate of Change.
"""

import numpy as np
from typing import List, Optional


class ConnorsRSI:
    """
    Connors RSI indicator.

    Formula:
    Connors RSI = (RSI(3) + RSI(Streak, 2) + ROC(100)) / 3
    """

    def __init__(self, rsi_period: int = 3, streak_period: int = 2, roc_period: int = 100):
        """
        Initialize Connors RSI indicator.

        Args:
            rsi_period: RSI period (default: 3)
            streak_period: Streak period (default: 2)
            roc_period: ROC period (default: 100)
        """
        self.rsi_period = rsi_period
        self.streak_period = streak_period
        self.roc_period = roc_period

    def calculate(self, closes: List[float]) -> Optional[float]:
        """
        Calculate Connors RSI for the given price series.

        Args:
            closes: List of close prices

        Returns:
            Connors RSI value (0-100) or None if insufficient data
        """
        if len(closes) < max(self.rsi_period, self.streak_period, self.roc_period) + 1:
            return None

        # RSI calculation (simplified)
        deltas = np.diff(closes[-self.rsi_period-1:])
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        avg_gain = np.mean(gains)
        avg_loss = np.mean(losses)
        if avg_loss == 0:
            rsi = 100
        else:
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))

        # Streak RSI (simplified)
        streak_rsi = rsi  # Placeholder

        # ROC
        if len(closes) < self.roc_period + 1:
            roc = 0
        else:
            roc = (closes[-1] - closes[-self.roc_period-1]) / closes[-self.roc_period-1] * 100

        # Connors RSI
        connors_rsi = (rsi + streak_rsi + roc) / 3
        return max(0, min(100, connors_rsi))

    def calculate_series(self, closes: List[float]) -> List[Optional[float]]:
        """
        Calculate Connors RSI for each point in the series.

        Args:
            closes: List of close prices

        Returns:
            List of Connors RSI values
        """
        connors_values = []
        for i in range(len(closes)):
            if i < max(self.rsi_period, self.streak_period, self.roc_period):
                connors_values.append(None)
            else:
                connors = self.calculate(closes[:i+1])
                connors_values.append(connors)
        return connors_values
