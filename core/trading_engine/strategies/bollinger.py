"""
Bollinger Bands strategies: mean reversion or breakout.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional

from ..indicators import bollinger_bands
from ..models import Bar, Signal, SignalAction
from ..strategy import BaseBarStrategy


@dataclass
class BollingerConfig:
    period: int = 20
    num_std: float = 2.0
    mode: str = "mean_reversion"  # or "breakout"


class BollingerBandsStrategy(BaseBarStrategy):
    def __init__(self, config: Optional[BollingerConfig] = None):
        super().__init__(name="bollinger_bands", lookback=500)
        self.config = config or BollingerConfig()
        self._in_position: Dict[str, bool] = {}

    def on_bar(self, bar: Bar) -> Optional[List[Signal]]:
        history = self.add_bar(bar)
        closes = [b.close for b in history]
        bands = bollinger_bands(closes, self.config.period, self.config.num_std)
        if not bands:
            return None

        mid, upper, lower = bands
        signals: List[Signal] = []
        in_position = self._in_position.get(bar.symbol, False)

        if self.config.mode == "mean_reversion":
            if bar.close <= lower and not in_position:
                signals.append(Signal(symbol=bar.symbol, action=SignalAction.BUY, confidence=self._confidence(lower, bar.close)))
                self._in_position[bar.symbol] = True
            elif bar.close >= mid and in_position:
                signals.append(Signal(symbol=bar.symbol, action=SignalAction.FLAT, confidence=1.0))
                self._in_position[bar.symbol] = False
        else:  # breakout
            if bar.close > upper and not in_position:
                signals.append(Signal(symbol=bar.symbol, action=SignalAction.BUY, confidence=1.0))
                self._in_position[bar.symbol] = True
            elif bar.close < mid and in_position:
                signals.append(Signal(symbol=bar.symbol, action=SignalAction.FLAT, confidence=1.0))
                self._in_position[bar.symbol] = False
        return signals

    def _confidence(self, lower_band: float, price: float) -> float:
        if lower_band == 0:
            return 0.5
        distance = (lower_band - price) / abs(lower_band)
        return min(abs(distance), 1.0)
