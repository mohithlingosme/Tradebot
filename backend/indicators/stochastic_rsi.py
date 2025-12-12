"""
Stochastic RSI Indicator

Applies stochastic oscillator formula to RSI values.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Sequence

import numpy as np


@dataclass
class StochasticRSI:
    """Stochastic RSI indicator."""

    rsi_period: int = 14
    stoch_period: int = 14
    k_period: int = 3
    d_period: int = 3

    def calculate(self, close: Sequence[float]) -> Optional[float]:
        """Return the StochRSI value for the latest period."""
        if len(close) < self.rsi_period + self.stoch_period:
            return None

        # Calculate RSI values
        rsi_values = self._calculate_rsi(close[-self.rsi_period - self.stoch_period:])

        # Apply stochastic to RSI
        if len(rsi_values) < self.stoch_period:
            return None

        highest_rsi = np.max(rsi_values[-self.stoch_period:])
        lowest_rsi = np.min(rsi_values[-self.stoch_period:])

        if highest_rsi == lowest_rsi:
            return 50.0

        stoch_rsi = ((rsi_values[-1] - lowest_rsi) / (highest_rsi - lowest_rsi)) * 100

        return float(stoch_rsi)

    def calculate_series(self, close: Sequence[float]) -> List[Optional[float]]:
        """Return StochRSI series."""
        stoch_rsi = []
        for i in range(len(close)):
            if i < self.rsi_period + self.stoch_period - 1:
                stoch_rsi.append(None)
            else:
                rsi_values = self._calculate_rsi(close[i - self.rsi_period - self.stoch_period + 1 : i + 1])
                highest_rsi = np.max(rsi_values[-self.stoch_period:])
                lowest_rsi = np.min(rsi_values[-self.stoch_period:])
                if highest_rsi == lowest_rsi:
                    stoch_rsi.append(50.0)
                else:
                    stoch_rsi_val = ((rsi_values[-1] - lowest_rsi) / (highest_rsi - lowest_rsi)) * 100
                    stoch_rsi.append(float(stoch_rsi_val))
        return stoch_rsi

    def _calculate_rsi(self, prices: Sequence[float]) -> List[float]:
        """Helper to calculate RSI."""
        deltas = np.diff(prices)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)

        rsi_values = []
        for i in range(len(prices)):
            if i < self.rsi_period:
                rsi_values.append(50.0)  # Neutral
            else:
                avg_gain = np.mean(gains[i - self.rsi_period + 1 : i + 1])
                avg_loss = np.mean(losses[i - self.rsi_period + 1 : i + 1])
                if avg_loss == 0:
                    rsi_values.append(100.0)
                else:
                    rs = avg_gain / avg_loss
                    rsi = 100 - (100 / (1 + rs))
                    rsi_values.append(rsi)
        return rsi_values
