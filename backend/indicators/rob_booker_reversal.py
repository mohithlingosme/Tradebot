"""
Rob Booker style reversal signal.

The canonical implementation uses a blend of moving averages and momentum.
This lightweight version flags reversals when price stretches beyond an EMA by
the configured percentage and then snaps back.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Sequence

from .moving_average import EMA


@dataclass
class RobBookerReversal:
    """Detect fast snap-back moves relative to an EMA."""

    ema_period: int = 34
    threshold_pct: float = 1.5

    def calculate(self, close: Sequence[float]) -> Optional[str]:
        values = self.calculate_series(close)
        return values[-1] if values else None

    def calculate_series(self, close: Sequence[float]) -> List[Optional[str]]:
        ema_indicator = EMA(self.ema_period)
        signals: List[Optional[str]] = []
        last_state: Optional[str] = None
        for idx in range(len(close)):
            ema_value = ema_indicator.calculate(list(close[: idx + 1]))
            if ema_value is None:
                signals.append(None)
                continue
            distance_pct = 100.0 * (close[idx] - ema_value) / ema_value if ema_value else 0.0
            signal: Optional[str] = None
            if distance_pct > self.threshold_pct:
                last_state = "overbought"
                signal = "stretch_up"
            elif distance_pct < -self.threshold_pct:
                last_state = "oversold"
                signal = "stretch_down"
            elif last_state == "overbought" and close[idx] < ema_value:
                signal = "bearish_reversal"
                last_state = None
            elif last_state == "oversold" and close[idx] > ema_value:
                signal = "bullish_reversal"
                last_state = None
            signals.append(signal)
        return signals
