"""
Strategy interfaces for the Phase 4 engine.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Protocol

from .models import Bar, Signal, Tick


class Strategy(Protocol):
    """Minimal strategy protocol for bars or ticks."""

    name: str

    def on_bar(self, bar: Bar) -> Optional[List[Signal]]:
        ...

    def on_tick(self, tick: Tick) -> Optional[List[Signal]]:
        ...


class BaseBarStrategy:
    """
    Helper base class that stores rolling bar history and exposes hooks.
    """

    def __init__(self, name: str, lookback: int = 250):
        self.name = name
        self.lookback = lookback
        self._history: Dict[str, List[Bar]] = {}

    def on_bar(self, bar: Bar) -> Optional[List[Signal]]:  # pragma: no cover - to be implemented by subclasses
        raise NotImplementedError

    def on_tick(self, tick: Tick) -> Optional[List[Signal]]:
        return None

    def add_bar(self, bar: Bar) -> List[Bar]:
        history = self._history.setdefault(bar.symbol, [])
        history.append(bar)
        if len(history) > self.lookback:
            history[:] = history[-self.lookback :]
        return history

    def get_history(self, symbol: str) -> List[Bar]:
        return list(self._history.get(symbol, []))
