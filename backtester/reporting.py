"""
Reporting and Analytics for Backtesting

Comprehensive performance metrics, breakdowns, and export functionality.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, date
from decimal import Decimal, ROUND_HALF_UP
import json
import csv
from pathlib import Path
import statistics
from collections import defaultdict

from .portfolio_accounting import PortfolioAccounting, TradeRecord, EquityPoint


@dataclass
class PerformanceMetrics:
    """Comprehensive performance metrics for backtest results."""

    # Basic returns
    total_return_pct: float = 0.0
    annualized_return_pct: float = 0.0
    cagr_pct: float = 0.0

    # Risk metrics
    volatility_pct: float = 0.0
    max_drawdown_pct: float = 0.0
    sharpe_ratio: float = 0.0
    sortino_ratio: float = 0.0
    calmar_ratio: float = 0.0

    # Trading metrics
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    win_rate_pct: float = 0.0
    profit_factor: float = 0.0
    expectancy: float = 0.0
    avg_win: float = 0.0
    avg_loss: float = 0.0
    largest_win: float = 0.0
    largest_loss: float = 0.0

    # Time-based metrics
    total_days: int = 0
    trading_days: int = 0
    avg_daily_return_pct: float = 0.0
    best_day_pct: float = 0.0
    worst_day_pct: float = 0.0

    # Risk-adjusted returns
    alpha: Optional[float] = None
    beta: Optional[float] = None
    information_ratio: Optional[float] = None

    # Additional metrics
    recovery_factor: float = 0.0
    payoff_ratio: float = 0.0
    kelly_criterion: float = 0.0

    # Additional metrics (already implemented above)
    cagr: float = 0.0
    expectancy: float = 0.0
    profit_factor: float = 0.0
    sortino_ratio: float = 0.0


@dataclass
class BreakdownMetrics:
    """Performance breakdown by symbol, period, or tag."""
    symbol: str
    period: Optional[str] = None
    tag: Optional[str] = None

    # Returns
    total_return_pct: float = 0.0
    annualized_return_pct: float = 0.0

    # Trading
    total_trades: int = 0
    win_rate_pct: float = 0.0
    profit_factor: float = 0.0

    # P&L
    total_pnl: float = 0.0
    realized_pnl: float = 0.0
    unrealized_pnl: float = 0.0

    # Risk
    max_drawdown_pct: float = 0.0
    volatility_pct: float = 0.0


@dataclass
class BacktestReport:
    """Complete backtest report."""
    run_id: str
    strategy_name: str
    symbols: List[str]
    start_date: date
    end_date: date
    initial_capital: float

    # Overall metrics
    metrics: PerformanceMetrics

    # Breakdowns
    symbol_breakdown: List[BreakdownMetrics] = field(default_factory=list)
    monthly_breakdown: List[BreakdownMetrics] = field(default_factory=list)
    tag_breakdown: List[BreakdownMetrics] = field(default_factory=list)

    # Raw data
    equity_curve: List[EquityPoint] = field(default_factory=list)
    trade_log: List[TradeRecord] = field(default_factory=list)

    # Metadata
    parameters: Dict[str, Any] = field(default_factory=dict)
    execution_time_seconds: float = 0.0
    generated_at: datetime = field(default_factory=datetime.utcnow)


class BacktestReporter:
    """
    Generates comprehensive reports and analytics from backtest results.

    Calculates performance metrics, breakdowns, and provides export functionality.
    """

    def __init__(self, portfolio: PortfolioAccounting):
        self.portfolio = portfolio

    def generate_report(self, run_id: str, strategy_name: str, symbols: List[str],
                       start_date: date, end_date: date, parameters: Dict[str, Any] = None) -> BacktestReport:
        """
        Generate complete backtest report.

        Args:
            run_id: Unique identifier for the backtest run
            strategy_name: Name of the strategy used
            symbols: List of symbols traded
            start_date: Backtest start date
            end_date: Backtest end date
            parameters: Strategy parameters used

        Returns:
            Complete backtest report with all metrics and breakdowns
        """
        parameters = parameters or {}

        # Calculate overall metrics
        metrics = self._calculate_performance_metrics()

        # Calculate breakdowns
        symbol_breakdown = self._calculate_symbol_breakdown()
        monthly_breakdown = self._calculate_monthly_breakdown()
        tag_breakdown = self._calculate_tag_breakdown()

        return BacktestReport(
            run_id=run_id,
            strategy_name=strategy_name,
            symbols=symbols,
            start_date=start_date,
            end_date=end_date,
            initial_capital=float(self.portfolio.initial_capital),
            metrics=metrics,
            symbol_breakdown=symbol_breakdown,
            monthly_breakdown=monthly_breakdown,
            tag_breakdown=tag_breakdown,
            equity_curve=self.portfolio.equity_curve.copy(),
            trade_log=self.portfolio.trade_log.copy(),
            parameters=parameters
        )

    def _calculate_performance_metrics(self, risk_free_rate: float = 0.0) -> PerformanceMetrics:
        """Calculate comprehensive performance metrics."""
        equity_curve = self.portfolio.equity_curve
        trade_log = self.portfolio.trade_log

        if not equity_curve:
            return PerformanceMetrics()

        # Basic return calculations
        initial_equity = equity_curve[0].equity
        final_equity = equity_curve[-1].equity
        total_return_pct = ((final_equity - initial_equity) / initial_equity) * 100

        # Time-based calculations
        start_date = equity_curve[0].timestamp.date()
        end_date = equity_curve[-1].timestamp.date()
        total_days = (end_date - start_date).days
        trading_days = len(set(ep.timestamp.date() for ep in equity_curve))

        # CAGR calculation
        if total_days > 0:
            years = total_days / 365.0
            cagr = ((final_equity / initial_equity) ** (1 / years) - 1) * 100
            annualized_return_pct = ((1 + total_return_pct / 100) ** (365 / total_days) - 1) * 100
        else:
            cagr = 0.0
            annualized_return_pct = 0.0

        # Daily returns for volatility and risk metrics
        daily_returns = []
        prev_equity = initial_equity

        for ep in equity_curve[1:]:
            daily_return = (ep.equity - prev_equity) / prev_equity
            daily_returns.append(daily_return)
            prev_equity = ep.equity

        # Volatility and risk metrics
        if daily_returns:
            volatility_pct = statistics.stdev(daily_returns) * (252 ** 0.5) * 100  # Annualized
            avg_daily_return_pct = statistics.mean(daily_returns) * 100

            # Sharpe ratio (using risk-free rate)
            excess_returns = [r - risk_free_rate/252 for r in daily_returns]  # Daily risk-free rate
            if volatility_pct > 0:
                sharpe_ratio = statistics.mean(excess_returns) / statistics.stdev(excess_returns) * (252 ** 0.5)
            else:
                sharpe_ratio = 0.0

            # Sortino ratio (downside deviation only, using risk-free rate)
            downside_returns = [r - risk_free_rate/252 for r in daily_returns if r < risk_free_rate/252]
            if downside_returns:
                downside_dev = statistics.stdev(downside_returns) * (252 ** 0.5)
                sortino_ratio = statistics.mean(excess_returns) / downside_dev if downside_dev > 0 else 0.0
            else:
                sortino_ratio = float('inf') if statistics.mean(excess_returns) > 0 else 0.0

            best_day_pct = max(daily_returns) * 100
            worst_day_pct = min(daily_returns) * 100
        else:
            volatility_pct = 0.0
            sharpe_ratio = 0.0
            sortino_ratio = 0.0
            avg_daily_return_pct = 0.0
            best_day_pct = 0.0
            worst_day_pct = 0.0

        # Max drawdown
        max_drawdown_pct = self.portfolio.max_drawdown_pct

        # Calmar ratio
        calmar_ratio = annualized_return_pct / max_drawdown_pct if max_drawdown_pct > 0 else 0.0

        # Trading metrics
        total_trades = len(trade_log)
        winning_trades = sum(1 for trade in trade_log if trade.realized_pnl > 0)
        losing_trades = sum(1 for trade in trade_log if trade.realized_pnl < 0)

        win_rate_pct = (winning_trades / total_trades * 100) if total_trades > 0 else 0.0

        # P&L metrics
        if trade_log:
            winning_pnls = [trade.realized_pnl for trade in trade_log if trade.realized_pnl > 0]
            losing_pnls = [trade.realized_pnl for trade in trade_log if trade.realized_pnl < 0]

            total_wins = sum(winning_pnls)
            total_losses = abs(sum(losing_pnls))

            profit_factor = total_wins / total_losses if total_losses > 0 else float('inf')

            avg_win = total_wins / len(winning_pnls) if winning_pnls else 0.0
            avg_loss = total_losses / len(losing_pnls) if losing_pnls else 0.0

            largest_win = max(winning_pnls) if winning_pnls else 0.0
            largest_loss = min(losing_pnls) if losing_pnls else 0.0

            # Expectancy (average win/loss per trade)
            win_prob = len(winning_pnls) / total_trades if total_trades > 0 else 0
            loss_prob = len(losing_pnls) / total_trades if total_trades > 0 else 0
            expectancy = (win_prob * avg_win) - (loss_prob * avg_loss)

            # Payoff ratio
            payoff_ratio = avg_win / abs(avg_loss) if avg_loss != 0 else float('inf')

            # Kelly criterion
            if win_prob > 0 and loss_prob > 0 and payoff_ratio > 0:
                kelly_criterion = win_prob - (loss_prob / payoff_ratio)
            else:
                kelly_criterion = 0.0
        else:
            profit_factor = 0.0
            avg_win = 0.0
            avg_loss = 0.0
            largest_win = 0.0
            largest_loss = 0.0
            expectancy = 0.0
            payoff_ratio = 0.0
            kelly_criterion = 0.0

        # Recovery factor
        total_return = final_equity - initial_equity
        recovery_factor = total_return / self.portfolio.max_drawdown if self.portfolio.max_drawdown > 0 else 0.0

        return PerformanceMetrics(
            total_return_pct=total_return_pct,
            annualized_return_pct=annualized_return_pct,
            cagr=cagr,
            volatility_pct=volatility_pct,
            max_drawdown_pct=max_drawdown_pct,
            sharpe_ratio=sharpe_ratio,
            sortino_ratio=sortino_ratio,
            calmar_ratio=calmar_ratio,
            total_trades=total_trades,
            winning_trades=winning_trades,
            losing_trades=losing_trades,
            win_rate_pct=win_rate_pct,
            profit_factor=profit_factor,
            expectancy=expectancy,
            avg_win=avg_win,
            avg_loss=avg_loss,
            largest_win=largest_win,
            largest_loss=largest_loss,
            total_days=total_days,
            trading_days=trading_days,
            avg_daily_return_pct=avg_daily_return_pct,
            best_day_pct=best_day_pct,
            worst_day_pct=worst_day_pct,
            recovery_factor=recovery_factor,
            payoff_ratio=payoff_ratio,
            kelly_criterion=kelly_criterion
        )

    def _calculate_symbol_breakdown(self) -> List[BreakdownMetrics]:
        """Calculate performance breakdown by symbol."""
        symbol_stats = defaultdict(lambda: {
            'trades': [], 'pnl': 0.0, 'realized_pnl': 0.0, 'unrealized_pnl': 0.0,
            'wins': 0, 'losses': 0, 'max_dd': 0.0, 'returns': []
        })

        # Aggregate trade data by symbol
        for trade in self.portfolio.trade_log:
            stats = symbol_stats[trade.symbol]
            stats['trades'].append(trade)
            stats['pnl'] += trade.realized_pnl
            stats['realized_pnl'] += trade.realized_pnl

            if trade.realized_pnl > 0:
                stats['wins'] += 1
            elif trade.realized_pnl < 0:
                stats['losses'] += 1

        # Calculate metrics for each symbol
        breakdowns = []
        for symbol, stats in symbol_stats.items():
            total_trades = len(stats['trades'])
            win_rate = (stats['wins'] / total_trades * 100) if total_trades > 0 else 0.0

            # Calculate profit factor
            wins_pnl = sum(t.realized_pnl for t in stats['trades'] if t.realized_pnl > 0)
            losses_pnl = abs(sum(t.realized_pnl for t in stats['trades'] if t.realized_pnl < 0))
            profit_factor = wins_pnl / losses_pnl if losses_pnl > 0 else float('inf')

            # Simplified return calculation (would need more sophisticated calculation for accuracy)
            total_return_pct = (stats['pnl'] / self.portfolio.initial_capital) * 100

            breakdowns.append(BreakdownMetrics(
                symbol=symbol,
                total_return_pct=total_return_pct,
                total_trades=total_trades,
                win_rate_pct=win_rate,
                profit_factor=profit_factor,
                total_pnl=stats['pnl'],
                realized_pnl=stats['realized_pnl'],
                unrealized_pnl=stats['unrealized_pnl']
            ))

        return breakdowns

    def _calculate_monthly_breakdown(self) -> List[BreakdownMetrics]:
        """Calculate performance breakdown by month."""
        monthly_stats = defaultdict(lambda: {
            'trades': [], 'pnl': 0.0, 'returns': []
        })

        # Aggregate by month
        for trade in self.portfolio.trade_log:
            month_key = f"{trade.exit_time.year}-{trade.exit_time.month:02d}"
            monthly_stats[month_key]['trades'].append(trade)
            monthly_stats[month_key]['pnl'] += trade.realized_pnl

        # Calculate metrics for each month
        breakdowns = []
        for period, stats in monthly_stats.items():
            total_trades = len(stats['trades'])
            wins = sum(1 for t in stats['trades'] if t.realized_pnl > 0)
            win_rate = (wins / total_trades * 100) if total_trades > 0 else 0.0

            breakdowns.append(BreakdownMetrics(
                symbol="",  # Not applicable for monthly
                period=period,
                total_return_pct=(stats['pnl'] / self.portfolio.initial_capital) * 100,
                total_trades=total_trades,
                win_rate_pct=win_rate,
                total_pnl=stats['pnl']
            ))

        return sorted(breakdowns, key=lambda x: x.period or "")

    def _calculate_tag_breakdown(self) -> List[BreakdownMetrics]:
        """Calculate performance breakdown by trade tags."""
        tag_stats = defaultdict(lambda: {
            'trades': [], 'pnl': 0.0
        })

        # Aggregate by tag
        for trade in self.portfolio.trade_log:
            for tag in trade.tags:
                tag_stats[tag]['trades'].append(trade)
                tag_stats[tag]['pnl'] += trade.realized_pnl

        # Calculate metrics for each tag
        breakdowns = []
        for tag, stats in tag_stats.items():
            total_trades = len(stats['trades'])
            wins = sum(1 for t in stats['trades'] if t.realized_pnl > 0)
            win_rate = (wins / total_trades * 100) if total_trades > 0 else 0.0

            breakdowns.append(BreakdownMetrics(
                symbol="",  # Not applicable for tags
                tag=tag,
                total_return_pct=(stats['pnl'] / self.portfolio.initial_capital) * 100,
                total_trades=total_trades,
                win_rate_pct=win_rate,
                total_pnl=stats['pnl']
            ))

        return breakdowns

    def export_json(self, report: BacktestReport, filepath: str) -> None:
        """Export report to JSON format."""
        def serialize_obj(obj):
            if hasattr(obj, '__dict__'):
                return {k: serialize_obj(v) for k, v in obj.__dict__.items()}
            elif isinstance(obj, (list, tuple)):
                return [serialize_obj(item) for item in obj]
            elif isinstance(obj, dict):
                return {k: serialize_obj(v) for k, v in obj.items()}
            elif isinstance(obj, (datetime, date)):
                return obj.isoformat()
            elif isinstance(obj, Decimal):
                return float(obj)
            else:
                return obj

        data = serialize_obj(report)

        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)

    def export_csv_trades(self, report: BacktestReport, filepath: str) -> None:
        """Export trade log to CSV format."""
        if not report.trade_log:
            return

        fieldnames = [
            'symbol', 'side', 'quantity', 'entry_price', 'exit_price',
            'entry_time', 'exit_time', 'realized_pnl', 'fees', 'tags'
        ]

        with open(filepath, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            for trade in report.trade_log:
                writer.writerow({
                    'symbol': trade.symbol,
                    'side': trade.side,
                    'quantity': trade.quantity,
                    'entry_price': float(trade.entry_price),
                    'exit_price': float(trade.exit_price),
                    'entry_time': trade.entry_time.isoformat(),
                    'exit_time': trade.exit_time.isoformat(),
                    'realized_pnl': float(trade.realized_pnl),
                    'fees': float(trade.fees),
                    'tags': ','.join(trade.tags)
                })

    def export_csv_equity(self, report: BacktestReport, filepath: str) -> None:
        """Export equity curve to CSV format."""
        if not report.equity_curve:
            return

        fieldnames = ['timestamp', 'equity', 'cash', 'fees', 'drawdown_pct']

        with open(filepath, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            for point in report.equity_curve:
                writer.writerow({
                    'timestamp': point.timestamp.isoformat(),
                    'equity': float(point.equity),
                    'cash': float(point.cash),
                    'fees': float(point.fees),
                    'drawdown_pct': point.drawdown_pct
                })

    def generate_html_report(self, report: BacktestReport, filepath: str) -> None:
        """Generate HTML report with charts and tables."""
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Backtest Report - {report.strategy_name}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .metric {{ background: #f5f5f5; padding: 10px; margin: 10px 0; border-radius: 5px; }}
                .metric-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 10px; }}
                table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
                .positive {{ color: green; }}
                .negative {{ color: red; }}
            </style>
        </head>
        <body>
            <h1>Backtest Report</h1>
            <h2>{report.strategy_name}</h2>

            <div class="metric">
                <h3>Overview</h3>
                <p><strong>Run ID:</strong> {report.run_id}</p>
                <p><strong>Period:</strong> {report.start_date} to {report.end_date}</p>
                <p><strong>Initial Capital:</strong> ₹{report.initial_capital:,.0f}</p>
                <p><strong>Symbols:</strong> {', '.join(report.symbols)}</p>
            </div>

            <div class="metric">
                <h3>Performance Metrics</h3>
                <div class="metric-grid">
                    <div><strong>Total Return:</strong> <span class="{'positive' if report.metrics.total_return_pct >= 0 else 'negative'}">{report.metrics.total_return_pct:.2f}%</span></div>
                    <div><strong>Annualized Return:</strong> <span class="{'positive' if report.metrics.annualized_return_pct >= 0 else 'negative'}">{report.metrics.annualized_return_pct:.2f}%</span></div>
                    <div><strong>Max Drawdown:</strong> <span class="negative">{report.metrics.max_drawdown_pct:.2f}%</span></div>
                    <div><strong>Sharpe Ratio:</strong> {report.metrics.sharpe_ratio:.2f}</div>
                    <div><strong>Win Rate:</strong> {report.metrics.win_rate_pct:.1f}%</div>
                    <div><strong>Profit Factor:</strong> {report.metrics.profit_factor:.2f}</div>
                    <div><strong>Total Trades:</strong> {report.metrics.total_trades}</div>
                    <div><strong>Expectancy:</strong> ₹{report.metrics.expectancy:,.0f}</div>
                </div>
            </div>

            <div class="metric">
                <h3>Risk Metrics</h3>
                <div class="metric-grid">
                    <div><strong>Volatility:</strong> {report.metrics.volatility_pct:.2f}%</div>
                    <div><strong>Sortino Ratio:</strong> {report.metrics.sortino_ratio:.2f}</div>
                    <div><strong>Calmar Ratio:</strong> {report.metrics.calmar_ratio:.2f}</div>
                    <div><strong>Recovery Factor:</strong> {report.metrics.recovery_factor:.2f}</div>
                    <div><strong>Payoff Ratio:</strong> {report.metrics.payoff_ratio:.2f}</div>
                    <div><strong>Kelly Criterion:</strong> {report.metrics.kelly_criterion:.2f}</div>
                </div>
            </div>

            <h3>Symbol Breakdown</h3>
            <table>
                <tr>
                    <th>Symbol</th>
                    <th>Total Return %</th>
                    <th>Trades</th>
                    <th>Win Rate %</th>
                    <th>Profit Factor</th>
                    <th>Total P&L</th>
                </tr>
                {"".join(f"<tr><td>{b.symbol}</td><td>{b.total_return_pct:.2f}%</td><td>{b.total_trades}</td><td>{b.win_rate_pct:.1f}%</td><td>{b.profit_factor:.2f}</td><td>₹{b.total_pnl:,.0f}</td></tr>" for b in report.symbol_breakdown)}
            </table>

            <h3>Recent Trades</h3>
            <table>
                <tr>
                    <th>Symbol</th>
                    <th>Side</th>
                    <th>Quantity</th>
                    <th>Entry Price</th>
                    <th>Exit Price</th>
                    <th>P&L</th>
                    <th>Entry Time</th>
                    <th>Exit Time</th>
                </tr>
                {"".join(f"<tr><td>{t.symbol}</td><td>{t.side}</td><td>{t.quantity}</td><td>₹{t.entry_price:,.1f}</td><td>₹{t.exit_price:,.1f}</td><td class={'positive' if t.realized_pnl >= 0 else 'negative'}>₹{t.realized_pnl:,.0f}</td><td>{t.entry_time.strftime('%Y-%m-%d %H:%M')}</td><td>{t.exit_time.strftime('%Y-%m-%d %H:%M')}</td></tr>" for t in report.trade_log[-20:])}
            </table>

            <div class="metric">
                <h3>Parameters</h3>
                <pre>{json.dumps(report.parameters, indent=2)}</pre>
            </div>

            <p><em>Report generated at: {report.generated_at.strftime('%Y-%m-%d %H:%M:%S UTC')}</em></p>
        </body>
        </html>
        """

        with open(filepath, 'w') as f:
            f.write(html_content)


# Example usage
if __name__ == "__main__":
    from .portfolio_accounting import PortfolioAccounting
    from datetime import date

    # Create sample portfolio
    portfolio = PortfolioAccounting(Decimal('100000'))

    # Add some sample data (would normally come from backtest run)
    reporter = BacktestReporter(portfolio)

    # Generate sample report
    report = reporter.generate_report(
        run_id="sample_run_001",
        strategy_name="SMA Crossover",
        symbols=["RELIANCE", "TCS"],
        start_date=date(2024, 1, 1),
        end_date=date(2024, 12, 31),
        parameters={"sma_fast": 20, "sma_slow": 50}
    )

    print(f"Total Return: {report.metrics.total_return_pct:.2f}%")
    print(f"Sharpe Ratio: {report.metrics.sharpe_ratio:.2f}")
    print(f"Win Rate: {report.metrics.win_rate_pct:.1f}%")
    print(f"Total Trades: {report.metrics.total_trades}")

    # Export to JSON
    reporter.export_json(report, "sample_report.json")
    print("Report exported to sample_report.json")
