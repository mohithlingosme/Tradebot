from datetime import datetime, timedelta
from typing import List, Tuple

from backtester import (
    BacktestConfig,
    CostModel,
    EventBacktester,
    WalkForwardConfig,
    WalkForwardRunner,
)
from trading_engine.phase4.models import Bar
from trading_engine.phase4.strategies import EMACrossoverConfig, EMACrossoverStrategy


def _sample_bars() -> Tuple[datetime, List[Bar]]:
    start = datetime(2023, 1, 1)
    closes = [10, 11, 12, 9, 8, 9, 11, 12, 10, 9]
    bars = [
        Bar(
            symbol="TEST",
            timestamp=start + timedelta(days=i),
            open=price,
            high=price + 0.5,
            low=price - 0.5,
            close=price,
            volume=1_000,
        )
        for i, price in enumerate(closes)
    ]
    return start, bars


def test_event_backtester_runs_with_costs():
    start, bars = _sample_bars()
    end = bars[-1].timestamp

    config = BacktestConfig(
        start=start,
        end=end,
        initial_capital=100_000,
        slippage_bps=5,
        commission_rate=0.001,
        fee_per_order=2.0,
        fee_per_unit=0.01,
    )
    cost_model = CostModel(slippage_bps=5, commission_rate=0.001, fee_per_order=2.0, fee_per_unit=0.01)
    strategy = EMACrossoverStrategy(EMACrossoverConfig(short_period=2, long_period=3))

    backtester = EventBacktester(config, strategies=[strategy], cost_model=cost_model)
    report = backtester.run(bars)

    assert report.trades
    assert report.performance.fees_paid > 0
    assert len(report.equity_curve) == len(bars) + 1
    assert report.performance.total_return > -1.0


def test_walk_forward_runner_yields_multiple_windows():
    start, bars = _sample_bars()
    base_config = BacktestConfig(start=start, end=bars[-1].timestamp, initial_capital=50_000)
    wf_config = WalkForwardConfig(window_size=5, step_size=3)
    runner = WalkForwardRunner(
        base_config=base_config,
        walk_config=wf_config,
        strategies_factory=lambda: [EMACrossoverStrategy(EMACrossoverConfig(short_period=2, long_period=3))],
    )

    reports = runner.run(bars)
    assert len(reports) >= 2
    assert any(r.trades for r in reports)
    for report in reports:
        assert report.equity_curve
