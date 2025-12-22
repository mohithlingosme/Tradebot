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
    exit_tolerance: float = 0.1  # exit when delta shrinks by 10%


class EMACrossoverStrategy(BaseBarStrategy):
    def __init__(self, config: Optional[EMACrossoverConfig] = None):
        super().__init__(name="ema_crossover", lookback=300)
        self.config = config or EMACrossoverConfig()
        self._trend_state = {}
        self._position_state = {}

    def on_bar(self, bar: Bar) -> Optional[List[Signal]]:
        history = self.add_bar(bar)
        closes = [b.close for b in history]

        short = ema(closes, self.config.short_period)
        long = ema(closes, self.config.long_period)
        if short is None or long is None:
            return None

        delta = short - long
        prev_delta = self._trend_state.get(bar.symbol)
        self._trend_state[bar.symbol] = delta
        signals: List[Signal] = []
        holding = self._position_state.get(bar.symbol, False)

        if delta > 0 and not holding and (prev_delta is None or prev_delta <= 0):
            signals.append(Signal(symbol=bar.symbol, action=SignalAction.BUY, confidence=self._confidence(short, long)))
            self._position_state[bar.symbol] = True

        exit_threshold = None
        if prev_delta is not None and prev_delta > 0:
            tol = max(0.0, min(self.config.exit_tolerance, 0.99))
            exit_threshold = prev_delta * (1 - tol)

        if holding and (
            delta <= 0
            or (exit_threshold is not None and delta < exit_threshold)
        ):
            signals.append(Signal(symbol=bar.symbol, action=SignalAction.FLAT, confidence=1.0))
            self._position_state[bar.symbol] = False
        return signals

    def _confidence(self, short: float, long: float) -> float:
        spread = (short - long) / long if long else 0.0
        return max(min(abs(spread) * 10, 1.0), self.config.min_confidence)
