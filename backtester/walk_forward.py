from __future__ import annotations

from typing import Callable, Iterable, List, Sequence, Union, Dict, Any
from datetime import datetime, date
from dataclasses import dataclass
from itertools import product
import statistics
import multiprocessing as mp
from concurrent.futures import ProcessPoolExecutor, as_completed

from trading_engine.phase4.strategy import Strategy

from .config import BacktestConfig, WalkForwardConfig
from .engine import EventBacktester, MarketEvent
from .reporting import BacktestReport


@dataclass
class ParameterSet:
    """Parameter set for optimization."""
    params: Dict[str, Any]
    train_performance: float = 0.0
    test_performance: float = 0.0
    oos_performance: float = 0.0


@dataclass
class WalkForwardWindow:
    """Walk-forward analysis window."""
    train_start: datetime
    train_end: datetime
    test_start: datetime
    test_end: datetime
    oos_start: datetime | None = None
    oos_end: datetime | None = None
    window_type: str = "rolling"  # "anchored" or "rolling"


@dataclass
class WalkForwardResult:
    """Complete walk-forward analysis result."""
    parameter_sets: List[ParameterSet]
    windows: List[WalkForwardWindow]
    best_params: Dict[str, Any]
    oos_metrics: Dict[str, float]
    robustness_score: float


class ParameterGridSearch:
    """Grid search for parameter optimization with multiprocessing support."""

    def __init__(self, param_ranges: Dict[str, List[Any]]):
        self.param_ranges = param_ranges

    def generate_parameter_sets(self) -> List[Dict[str, Any]]:
        """Generate all combinations of parameters."""
        param_names = list(self.param_ranges.keys())
        param_values = list(self.param_ranges.values())

        combinations = product(*param_values)
        return [dict(zip(param_names, combo)) for combo in combinations]

    def generate_parameter_sets_generator(self):
        """Generate parameter sets as a generator for memory efficiency."""
        param_names = list(self.param_ranges.keys())
        param_values = list(self.param_ranges.values())

        for combo in product(*param_values):
            yield dict(zip(param_names, combo))


class WalkForwardAnalyzer:
    """Advanced walk-forward analysis with parameter optimization."""

    def __init__(self, strategy_class: type, base_config: BacktestConfig,
                 walk_config: WalkForwardConfig, param_ranges: Dict[str, List[Any]] = None):
        self.strategy_class = strategy_class
        self.base_config = base_config
        self.walk_config = walk_config
        self.param_ranges = param_ranges or {}
        self.parameter_search = ParameterGridSearch(self.param_ranges) if self.param_ranges else None

    def generate_windows(self, start_date: date, end_date: date, window_type: str = "rolling") -> List[WalkForwardWindow]:
        """Generate walk-forward windows with support for anchored/rolling types."""
        windows = []
        current_train_end = start_date

        while current_train_end < end_date:
            if window_type == "anchored":
                # Anchored: training period stays fixed, only test period moves
                train_start = start_date
                train_end = min(start_date + self.walk_config.train_period, end_date)
                test_start = current_train_end
                test_end = min(test_start + self.walk_config.test_period, end_date)
            else:  # rolling
                # Rolling: both training and test periods move forward
                train_start = current_train_end
                train_end = min(train_start + self.walk_config.train_period, end_date)
                test_start = train_end
                test_end = min(test_start + self.walk_config.test_period, end_date)

            # Out-of-sample period (optional)
            oos_start = test_end if self.walk_config.oos_period else None
            oos_end = min(oos_start + self.walk_config.oos_period, end_date) if oos_start else None

            if test_end > start_date:  # Ensure we have at least a test period
                windows.append(WalkForwardWindow(
                    train_start=datetime.combine(train_start, datetime.min.time()),
                    train_end=datetime.combine(train_end, datetime.max.time()),
                    test_start=datetime.combine(test_start, datetime.min.time()),
                    test_end=datetime.combine(test_end, datetime.max.time()),
                    oos_start=datetime.combine(oos_start, datetime.min.time()) if oos_start else None,
                    oos_end=datetime.combine(oos_end, datetime.max.time()) if oos_end else None,
                    window_type=window_type
                ))

            # Move to next window
            current_train_end = test_end

        return windows

    def run_parameter_optimization(self, events: Union[Dict[str, Sequence[MarketEvent]], Iterable[MarketEvent]],
                                  windows: List[WalkForwardWindow]) -> List[ParameterSet]:
        """Run parameter optimization across walk-forward windows."""
        if not self.parameter_search:
            return []

        param_sets = []
        normalized_events = EventBacktester._normalize_events(events)

        # Use generator for memory efficiency with large parameter spaces
        for params in self.parameter_search.generate_parameter_sets_generator():
            train_performances = []
            test_performances = []
            oos_performances = []

            for window in windows:
                # Training phase
                train_events = [e for e in normalized_events
                              if window.train_start <= e.timestamp <= window.train_end]
                if not train_events:
                    continue

                train_config = self.base_config.copy_with(
                    start=window.train_start,
                    end=window.train_end
                )

                strategy = self.strategy_class(**params)
                backtester = EventBacktester(train_config, strategies=[strategy])
                train_report = backtester.run(train_events)
                train_perf = self._calculate_performance_metric(train_report)
                train_performances.append(train_perf)

                # Testing phase (in-sample)
                test_events = [e for e in normalized_events
                             if window.test_start <= e.timestamp <= window.test_end]
                if test_events:
                    test_config = self.base_config.copy_with(
                        start=window.test_start,
                        end=window.test_end
                    )
                    backtester = EventBacktester(test_config, strategies=[strategy])
                    test_report = backtester.run(test_events)
                    test_perf = self._calculate_performance_metric(test_report)
                    test_performances.append(test_perf)

                # Out-of-sample phase
                if window.oos_start and window.oos_end:
                    oos_events = [e for e in normalized_events
                                if window.oos_start <= e.timestamp <= window.oos_end]
                    if oos_events:
                        oos_config = self.base_config.copy_with(
                            start=window.oos_start,
                            end=window.oos_end
                        )
                        backtester = EventBacktester(oos_config, strategies=[strategy])
                        oos_report = backtester.run(oos_events)
                        oos_perf = self._calculate_performance_metric(oos_report)
                        oos_performances.append(oos_perf)

            # Aggregate performances
            avg_train = statistics.mean(train_performances) if train_performances else 0
            avg_test = statistics.mean(test_performances) if test_performances else 0
            avg_oos = statistics.mean(oos_performances) if oos_performances else 0

            param_sets.append(ParameterSet(
                params=params,
                train_performance=avg_train,
                test_performance=avg_test,
                oos_performance=avg_oos
            ))

        return param_sets

    def _calculate_performance_metric(self, report: BacktestReport) -> float:
        """Calculate primary performance metric for optimization."""
        # Use Sharpe ratio as primary metric, fallback to total return
        if hasattr(report, 'metrics') and report.metrics.sharpe_ratio != 0:
            return report.metrics.sharpe_ratio
        elif hasattr(report, 'metrics'):
            return report.metrics.total_return_pct
        else:
            return 0.0

    def analyze_robustness(self, param_sets: List[ParameterSet]) -> Dict[str, Any]:
        """Analyze parameter robustness and overfitting."""
        if not param_sets:
            return {}

        # Calculate overfitting metrics
        oos_performances = [ps.oos_performance for ps in param_sets if ps.oos_performance != 0]
        train_performances = [ps.train_performance for ps in param_sets]

        if not oos_performances:
            return {
                'overfitting_ratio': 0.0,
                'robustness_score': 0.0,
                'best_oos_performance': 0.0
            }

        # Overfitting ratio (train/test performance difference)
        avg_train = statistics.mean(train_performances)
        avg_oos = statistics.mean(oos_performances)
        overfitting_ratio = avg_train / avg_oos if avg_oos != 0 else float('inf')

        # Robustness score (consistency of OOS performance)
        if len(oos_performances) > 1:
            robustness_score = 1.0 / (1.0 + statistics.stdev(oos_performances) / abs(statistics.mean(oos_performances)))
        else:
            robustness_score = 1.0

        best_oos = max(oos_performances)

        return {
            'overfitting_ratio': overfitting_ratio,
            'robustness_score': robustness_score,
            'best_oos_performance': best_oos,
            'avg_oos_performance': avg_oos,
            'oos_std_dev': statistics.stdev(oos_performances) if len(oos_performances) > 1 else 0.0
        }

    def run_full_analysis(self, events: Union[Dict[str, Sequence[MarketEvent]], Iterable[MarketEvent]],
                         start_date: date, end_date: date) -> WalkForwardResult:
        """Run complete walk-forward analysis with parameter optimization."""
        windows = self.generate_windows(start_date, end_date)
        param_sets = self.run_parameter_optimization(events, windows)

        # Find best parameters based on OOS performance
        best_param_set = max(param_sets, key=lambda ps: ps.oos_performance) if param_sets else None
        best_params = best_param_set.params if best_param_set else {}

        # Analyze robustness
        robustness_metrics = self.analyze_robustness(param_sets)

        return WalkForwardResult(
            parameter_sets=param_sets,
            windows=windows,
            best_params=best_params,
            oos_metrics=robustness_metrics,
            robustness_score=robustness_metrics.get('robustness_score', 0.0)
        )


class WalkForwardEngine:
    """Walk-forward engine supporting chronological train/test splits."""

    def __init__(self, base_config: BacktestConfig, walk_config: WalkForwardConfig):
        self.base_config = base_config
        self.walk_config = walk_config

    def run_walk_forward(self, strategy_class: type, events: Union[Dict[str, Sequence[MarketEvent]], Iterable[MarketEvent]],
                        param_ranges: Dict[str, List[Any]] = None, max_workers: int = None) -> WalkForwardResult:
        """
        Run walk-forward analysis with chronological splits.

        Args:
            strategy_class: Strategy class to optimize
            events: Market events for backtesting
            param_ranges: Parameter ranges for grid search
            max_workers: Number of parallel workers for grid search

        Returns:
            WalkForwardResult with optimization results
        """
        analyzer = WalkForwardAnalyzer(strategy_class, self.base_config, self.walk_config, param_ranges)

        # Generate windows
        normalized_events = EventBacktester._normalize_events(events)
        if not normalized_events:
            return WalkForwardResult([], [], {}, {}, 0.0)

        start_date = normalized_events[0].timestamp.date()
        end_date = normalized_events[-1].timestamp.date()

        windows = analyzer.generate_windows(start_date, end_date)

        # Run parameter optimization (potentially parallel)
        if max_workers and max_workers > 1 and param_ranges:
            param_sets = self._run_parallel_optimization(analyzer, events, windows, max_workers)
        else:
            param_sets = analyzer.run_parameter_optimization(events, windows)

        # Find best parameters and analyze robustness
        best_param_set = max(param_sets, key=lambda ps: ps.oos_performance) if param_sets else None
        best_params = best_param_set.params if best_param_set else {}

        robustness_metrics = analyzer.analyze_robustness(param_sets)

        return WalkForwardResult(
            parameter_sets=param_sets,
            windows=windows,
            best_params=best_params,
            oos_metrics=robustness_metrics,
            robustness_score=robustness_metrics.get('robustness_score', 0.0)
        )

    def _run_parallel_optimization(self, analyzer: WalkForwardAnalyzer, events: Union[Dict[str, Sequence[MarketEvent]], Iterable[MarketEvent]],
                                  windows: List[WalkForwardWindow], max_workers: int) -> List[ParameterSet]:
        """Run parameter optimization in parallel using multiprocessing."""
        if not analyzer.parameter_search:
            return []

        param_sets = []

        # Use ProcessPoolExecutor with chunksize for memory efficiency
        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            # Submit all parameter combinations
            future_to_params = {}
            for params in analyzer.parameter_search.generate_parameter_sets_generator():
                future = executor.submit(self._evaluate_param_set, analyzer, params, events, windows)
                future_to_params[future] = params

            # Collect results as they complete (memory efficient)
            for future in as_completed(future_to_params):
                try:
                    param_set = future.result()
                    param_sets.append(param_set)
                except Exception as exc:
                    params = future_to_params[future]
                    print(f'Parameter set {params} generated an exception: {exc}')
                    # Add failed parameter set with zero performance
                    param_sets.append(ParameterSet(params=params, train_performance=0, test_performance=0, oos_performance=0))

        return param_sets

    @staticmethod
    def _evaluate_param_set(analyzer: WalkForwardAnalyzer, params: Dict[str, Any],
                           events: Union[Dict[str, Sequence[MarketEvent]], Iterable[MarketEvent]],
                           windows: List[WalkForwardWindow]) -> ParameterSet:
        """Evaluate a single parameter set across all windows."""
        train_performances = []
        test_performances = []
        oos_performances = []

        normalized_events = EventBacktester._normalize_events(events)

        for window in windows:
            # Training phase
            train_events = [e for e in normalized_events
                          if window.train_start <= e.timestamp <= window.train_end]
            if not train_events:
                continue

            train_config = analyzer.base_config.copy_with(
                start=window.train_start,
                end=window.train_end
            )

            strategy = analyzer.strategy_class(**params)
            backtester = EventBacktester(train_config, strategies=[strategy])
            train_report = backtester.run(train_events)
            train_perf = analyzer._calculate_performance_metric(train_report)
            train_performances.append(train_perf)

            # Testing phase (in-sample)
            test_events = [e for e in normalized_events
                         if window.test_start <= e.timestamp <= window.test_end]
            if test_events:
                test_config = analyzer.base_config.copy_with(
                    start=window.test_start,
                    end=window.test_end
                )
                backtester = EventBacktester(test_config, strategies=[strategy])
                test_report = backtester.run(test_events)
                test_perf = analyzer._calculate_performance_metric(test_report)
                test_performances.append(test_perf)

            # Out-of-sample phase
            if window.oos_start and window.oos_end:
                oos_events = [e for e in normalized_events
                            if window.oos_start <= e.timestamp <= window.oos_end]
                if oos_events:
                    oos_config = analyzer.base_config.copy_with(
                        start=window.oos_start,
                        end=window.oos_end
                    )
                    backtester = EventBacktester(oos_config, strategies=[strategy])
                    oos_report = backtester.run(oos_events)
                    oos_perf = analyzer._calculate_performance_metric(oos_report)
                    oos_performances.append(oos_perf)

        # Aggregate performances
        avg_train = statistics.mean(train_performances) if train_performances else 0
        avg_test = statistics.mean(test_performances) if test_performances else 0
        avg_oos = statistics.mean(oos_performances) if oos_performances else 0

        return ParameterSet(
            params=params,
            train_performance=avg_train,
            test_performance=avg_test,
            oos_performance=avg_oos
        )


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
