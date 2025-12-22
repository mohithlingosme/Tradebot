"""
Adaptive RSI + MACD hybrid strategy.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional

from ..indicators import macd, rsi
from ..models import Bar, Signal, SignalAction
from ..strategy import BaseBarStrategy


@dataclass
class AdaptiveHybridConfig:
    rsi_period: int = 14
    rsi_entry: float = 40.0
    rsi_exit: float = 65.0
    macd_fast: int = 12
    macd_slow: int = 26
    macd_signal: int = 9


class AdaptiveRSIMACDHybridStrategy(BaseBarStrategy):
    def __init__(self, config: Optional[AdaptiveHybridConfig] = None):
        super().__init__(name="adaptive_rsi_macd_hybrid", lookback=500)
        self.config = config or AdaptiveHybridConfig()
        self._in_position: Dict[str, bool] = {}

    def on_bar(self, bar: Bar) -> Optional[List[Signal]]:
        history = self.add_bar(bar)
        closes = [b.close for b in history]

        rsi_value = rsi(closes, self.config.rsi_period)
        macd_data = macd(closes, self.config.macd_fast, self.config.macd_slow, self.config.macd_signal)
        if rsi_value is None or not macd_data:
            return None

        hist = macd_data["histogram"]
        in_position = self._in_position.get(bar.symbol, False)
        signals: List[Signal] = []

        # Trend filter via MACD histogram direction
        if hist > 0 and rsi_value < self.config.rsi_entry and not in_position:
            confidence = self._confidence(hist, rsi_value, bullish=True)
            signals.append(Signal(symbol=bar.symbol, action=SignalAction.BUY, confidence=confidence))
            self._in_position[bar.symbol] = True
        elif (hist < 0 or rsi_value > self.config.rsi_exit) and in_position:
            signals.append(Signal(symbol=bar.symbol, action=SignalAction.FLAT, confidence=1.0))
            self._in_position[bar.symbol] = False
        return signals

    def _confidence(self, histogram: float, rsi_value: float, bullish: bool) -> float:
        rsi_gap = (self.config.rsi_entry - rsi_value) / self.config.rsi_entry if bullish else 0.0
        macd_strength = min(abs(histogram), 1.0)
        return min(max(0.1, 0.5 * macd_strength + 0.5 * max(rsi_gap, 0.0)), 1.0)
