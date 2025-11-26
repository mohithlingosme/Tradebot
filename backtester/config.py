from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from trading_engine.phase4.position_sizing import PositionSizer
from trading_engine.phase4.risk import RiskLimits


@dataclass
class BacktestConfig:
    """Runtime configuration for a single backtest run."""

    start: datetime
    end: datetime
    initial_capital: float = 100_000.0
    slippage_bps: float = 1.0
    commission_rate: float = 0.0005
    fee_per_order: float = 0.0
    fee_per_unit: float = 0.0
    report_dir: str = "backtest_results"
    risk_limits: RiskLimits = field(default_factory=RiskLimits)
    position_sizer: PositionSizer = field(default_factory=PositionSizer)
    risk_free_rate: float = 0.0

    def copy_with(self, start: datetime, end: datetime) -> "BacktestConfig":
        """Return a shallow copy with updated date bounds."""
        return BacktestConfig(
            start=start,
            end=end,
            initial_capital=self.initial_capital,
            slippage_bps=self.slippage_bps,
            commission_rate=self.commission_rate,
            fee_per_order=self.fee_per_order,
            fee_per_unit=self.fee_per_unit,
            report_dir=self.report_dir,
            risk_limits=self.risk_limits,
            position_sizer=self.position_sizer,
            risk_free_rate=self.risk_free_rate,
        )


@dataclass
class WalkForwardConfig:
    """Parameters for walk-forward backtesting."""

    window_size: int
    step_size: Optional[int] = None

    def effective_step(self) -> int:
        if self.step_size is not None and self.step_size > 0:
            return self.step_size
        return max(1, self.window_size // 2)
