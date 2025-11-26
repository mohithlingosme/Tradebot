"""
Backtesting runner built on top of the Phase 4 engine components.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from .engine import TradingEngine
from .metrics import PerformanceMetrics, calculate_performance
from .models import Bar, OrderFill, PortfolioState
from .paper_engine import PaperTradingEngine
from .position_sizing import PositionSizer
from .risk import RiskLimits, RiskManager
from .strategy import Strategy


@dataclass
class BacktestConfig:
    start: datetime
    end: datetime
    initial_capital: float = 100_000.0
    slippage_bps: float = 1.0
    commission_rate: float = 0.0005
    risk_limits: RiskLimits = field(default_factory=RiskLimits)
    report_dir: str = "backtest_results"


@dataclass
class BacktestReport:
    metrics: PerformanceMetrics
    trades: List[OrderFill]
    equity_curve: List[Tuple[datetime, float]]


class HistoricalDataLoader:
    """Loads historical OHLCV either from CSV files or preloaded data structures."""

    def load_history(
        self,
        symbols: List[str],
        start: datetime,
        end: datetime,
        timeframe: str,
        source_path: Optional[str] = None,
    ) -> Dict[str, List[Bar]]:
        bars: Dict[str, List[Bar]] = {s: [] for s in symbols}
        if source_path:
            for symbol in symbols:
                file_path = Path(source_path) / f"{symbol}_{timeframe}.csv"
                if not file_path.exists():
                    continue
                try:
                    import pandas as pd  # type: ignore
                except ModuleNotFoundError as exc:  # pragma: no cover - optional dependency
                    raise ModuleNotFoundError("pandas is required to load history from CSV files") from exc
                df = pd.read_csv(file_path, parse_dates=["timestamp"])
                for _, row in df.iterrows():
                    ts: datetime = row["timestamp"].to_pydatetime() if hasattr(row["timestamp"], "to_pydatetime") else row["timestamp"]
                    if ts < start or ts > end:
                        continue
                    bars[symbol].append(
                        Bar(
                            symbol=symbol,
                            timestamp=ts,
                            open=float(row["open"]),
                            high=float(row["high"]),
                            low=float(row["low"]),
                            close=float(row["close"]),
                            volume=float(row.get("volume", 0.0)),
                        )
                    )
        return bars


class BacktestRunner:
    """Runs backtests using the shared trading engine components."""

    def __init__(
        self,
        config: BacktestConfig,
        position_sizer: Optional[PositionSizer] = None,
    ):
        self.config = config
        self.position_sizer = position_sizer or PositionSizer()

    def run(self, strategies: List[Strategy], bars_by_symbol: Dict[str, List[Bar]]) -> BacktestReport:
        portfolio = self._create_portfolio()
        risk_manager = RiskManager(self.config.risk_limits)
        paper_engine = PaperTradingEngine(portfolio=portfolio, slippage_bps=self.config.slippage_bps, commission_rate=self.config.commission_rate)
        engine = TradingEngine(
            strategies=strategies,
            risk_manager=risk_manager,
            paper_engine=paper_engine,
            position_sizer=self.position_sizer,
        )

        for bar in self._iter_bars(bars_by_symbol):
            if bar.timestamp < self.config.start or bar.timestamp > self.config.end:
                continue
            engine.on_bar(bar)

        metrics = calculate_performance(engine.equity_curve, paper_engine.logs.trades)
        return BacktestReport(metrics=metrics, trades=list(paper_engine.logs.trades), equity_curve=list(engine.equity_curve))

    def _iter_bars(self, bars_by_symbol: Dict[str, List[Bar]]):
        """Yield bars ordered by timestamp across all symbols."""
        combined: List[Bar] = []
        for symbol, bars in bars_by_symbol.items():
            combined.extend(bars)
        combined.sort(key=lambda b: b.timestamp)
        return combined

    def _create_portfolio(self) -> PortfolioState:
        return PortfolioState(cash=self.config.initial_capital, daily_start_equity=self.config.initial_capital)
