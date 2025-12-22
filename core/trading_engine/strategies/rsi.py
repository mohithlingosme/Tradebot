"""
RSI-based overbought/oversold strategy.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional

from ..indicators import rsi
from ..models import Bar, Signal, SignalAction
from ..strategy import BaseBarStrategy


@dataclass
class RSIConfig:
    period: int = 14
    oversold: float = 30.0
    overbought: float = 70.0


class RSIStrategy(BaseBarStrategy):
    def __init__(self, config: Optional[RSIConfig] = None):
        super().__init__(name="rsi", lookback=400)
        self.config = config or RSIConfig()
        self._in_position: Dict[str, bool] = {}

    def on_bar(self, bar: Bar) -> Optional[List[Signal]]:
        history = self.add_bar(bar)
        closes = [b.close for b in history]
        rsi_value = rsi(closes, self.config.period)
        if rsi_value is None:
            return None

        signals: List[Signal] = []
        in_position = self._in_position.get(bar.symbol, False)

        if rsi_value < self.config.oversold and not in_position:
            signals.append(Signal(symbol=bar.symbol, action=SignalAction.BUY, confidence=self._confidence(self.config.oversold - rsi_value)))
            self._in_position[bar.symbol] = True
        elif rsi_value > self.config.overbought and in_position:
            signals.append(Signal(symbol=bar.symbol, action=SignalAction.FLAT, confidence=1.0))
            self._in_position[bar.symbol] = False
        return signals

    def _confidence(self, distance: float) -> float:
        return min(distance / 30, 1.0)
