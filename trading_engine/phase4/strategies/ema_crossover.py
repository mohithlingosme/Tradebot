"""
EMA crossover strategy (long-only by default).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from ..indicators import ema
from ..models import Bar, Signal, SignalAction
from ..strategy import BaseBarStrategy


@dataclass
class EMACrossoverConfig:
    short_period: int = 9
    long_period: int = 21
    min_confidence: float = 0.0


class EMACrossoverStrategy(BaseBarStrategy):
    def __init__(self, config: Optional[EMACrossoverConfig] = None):
        super().__init__(name="ema_crossover", lookback=300)
        self.config = config or EMACrossoverConfig()
        self._trend_state = {}

    def on_bar(self, bar: Bar) -> Optional[List[Signal]]:
        history = self.add_bar(bar)
        closes = [b.close for b in history]

        short = ema(closes, self.config.short_period)
        long = ema(closes, self.config.long_period)
        if short is None or long is None:
            return None

        prev_state = self._trend_state.get(bar.symbol)
        signals: List[Signal] = []

        if short > long and prev_state != "long":
            signals.append(Signal(symbol=bar.symbol, action=SignalAction.BUY, confidence=self._confidence(short, long)))
            self._trend_state[bar.symbol] = "long"
        elif short < long and prev_state == "long":
            signals.append(Signal(symbol=bar.symbol, action=SignalAction.FLAT, confidence=1.0))
            self._trend_state[bar.symbol] = "flat"
        return signals

    def _confidence(self, short: float, long: float) -> float:
        spread = (short - long) / long if long else 0.0
        return max(min(abs(spread) * 10, 1.0), self.config.min_confidence)
