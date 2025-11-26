from __future__ import annotations

"""Simple registry for discovering available strategies."""

from typing import Dict

from strategies.base import Strategy


class StrategyRegistry:
    """Register and retrieve strategy classes by name."""

    def __init__(self) -> None:
        self._registry: Dict[str, type[Strategy]] = {}

    def register(self, name: str, cls: type[Strategy]) -> None:
        if name in self._registry:
            raise ValueError(f"Strategy {name} already registered")
        self._registry[name] = cls

    def get(self, name: str) -> type[Strategy]:
        return self._registry[name]

    def list_strategies(self) -> list[str]:
        return list(self._registry.keys())


registry = StrategyRegistry()

