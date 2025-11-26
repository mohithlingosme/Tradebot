"""
MACD crossover strategy.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from ..indicators import macd
from ..models import Bar, Signal, SignalAction
from ..strategy import BaseBarStrategy


@dataclass
class MACDConfig:
    fast: int = 12
    slow: int = 26
    signal: int = 9


class MACDStrategy(BaseBarStrategy):
    def __init__(self, config: Optional[MACDConfig] = None):
        super().__init__(name="macd", lookback=400)
        self.config = config or MACDConfig()
        self._prev_hist = {}

    def on_bar(self, bar: Bar) -> Optional[List[Signal]]:
        history = self.add_bar(bar)
        closes = [b.close for b in history]
        macd_data = macd(closes, self.config.fast, self.config.slow, self.config.signal)
        if not macd_data:
            return None

        hist = macd_data["histogram"]
        prev_hist = self._prev_hist.get(bar.symbol)
        self._prev_hist[bar.symbol] = hist

        signals: List[Signal] = []
        if prev_hist is None:
            return None

        if hist > 0 and prev_hist <= 0:
            signals.append(Signal(symbol=bar.symbol, action=SignalAction.BUY, confidence=self._confidence(hist)))
        elif hist < 0 and prev_hist >= 0:
            signals.append(Signal(symbol=bar.symbol, action=SignalAction.FLAT, confidence=1.0))
        return signals

    def _confidence(self, histogram: float) -> float:
        return min(abs(histogram), 1.0)
