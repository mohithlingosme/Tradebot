from __future__ import annotations

from typing import Callable, Iterable, List, Sequence, Union

from trading_engine.phase4.strategy import Strategy

from .config import BacktestConfig, WalkForwardConfig
from .engine import EventBacktester, MarketEvent
from .reporting import BacktestReport


class WalkForwardRunner:
    """Sequential walk-forward runner using the event-based backtester."""

    def __init__(
        self,
        base_config: BacktestConfig,
        walk_config: WalkForwardConfig,
        strategies_factory: Callable[[], Sequence[Strategy]],
    ):
        self.base_config = base_config
        self.walk_config = walk_config
        self.strategies_factory = strategies_factory

    def run(self, events: Union[dict, Iterable[MarketEvent]]) -> List[BacktestReport]:
        normalized = EventBacktester._normalize_events(events)
        results: List[BacktestReport] = []

        window = self.walk_config.window_size
        step = self.walk_config.effective_step()

        start_idx = 0
        while start_idx < len(normalized):
            window_events = normalized[start_idx : start_idx + window]
            if len(window_events) < 2:
                break

            window_config = self.base_config.copy_with(
                start=window_events[0].timestamp,
                end=window_events[-1].timestamp,
            )
            backtester = EventBacktester(window_config, strategies=self.strategies_factory())
            results.append(backtester.run(window_events))

            start_idx += step

        return results
