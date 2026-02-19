"""
Command Line Interface for Backtesting

Provides CLI commands for running backtests, managing data, and generating reports.
"""

import argparse
import sys
from pathlib import Path
from datetime import date, datetime
from typing import List, Dict, Any, Optional
import json
import time
import concurrent.futures
import hashlib
from functools import lru_cache

from .performance import BatchBacktester, BatchJob
from .walk_forward import WalkForwardAnalyzer, ParameterGridSearch, ValidationReport
from .reporting import BacktestReporter
from .strategy_interface import create_strategy
from .ohlcv_storage import OHLCVStorage
from .instrument_master import InstrumentMaster


class IndicatorCache:
    """Cache for technical indicators to avoid redundant computation during grid searches."""

    def __init__(self, maxsize: int = 10000):
        self.cache = {}
        self.maxsize = maxsize

    def get_key(self, symbol: str, timeframe: str, indicator_name: str, parameters: Dict[str, Any]) -> str:
        """Generate cache key for indicator."""
        param_hash = hashlib.md5(str(sorted(parameters.items())).encode()).hexdigest()
        return f"{symbol}_{timeframe}_{indicator_name}_{param_hash}"

    def get_indicator(self, symbol: str, timeframe: str, indicator_name: str, parameters: Dict[str, Any], data):
        """Get cached indicator or compute if not cached."""
        key = self.get_key(symbol, timeframe, indicator_name, parameters)

        if key in self.cache:
            return self.cache[key]

        # Compute indicator (placeholder - would call actual indicator function)
        result = self._compute_indicator(indicator_name, data, **parameters)

        # Cache with LRU eviction
        if len(self.cache) >= self.maxsize:
            # Simple LRU: remove oldest (in practice, use a proper LRU cache)
            oldest_key = next(iter(self.cache))
            del self.cache[oldest_key]

        self.cache[key] = result
        return result

    def _compute_indicator(self, name: str, data, **params):
        """Placeholder for indicator computation."""
        # This would call the actual indicator library
        return f"computed_{name}_{hash(str(params))}"

    def clear(self):
        """Clear the cache."""
        self.cache.clear()


class BacktestCLI:
    """
    Command Line Interface for backtesting operations.

    Provides commands for:
    - Running single backtests
    - Batch backtesting
    - Walk-forward analysis
    - Data management
    - Report generation
    """

    def __init__(self):
        self.storage = OHLCVStorage()
        self.instrument_master = InstrumentMaster()
        self.batch_backtester = BatchBacktester(self._run_single_backtest)
        self.indicator_cache = IndicatorCache()

    def run(self, args: Optional[List[str]] = None) -> None:
        """Main CLI entry point."""
        parser = self._create_parser()

        if args is None:
            args = sys.argv[1:]

        parsed_args = parser.parse_args(args)

        if not hasattr(parsed_args, 'command'):
            parser.print_help()
            return

        # Execute the appropriate command
        command_method = getattr(self, f"_cmd_{parsed_args.command}", None)
        if command_method:
            try:
                command_method(parsed_args)
            except Exception as e:
                print(f"Error: {e}", file=sys.stderr)
                sys.exit(1)
        else:
            print(f"Unknown command: {parsed_args.command}", file=sys.stderr)
            sys.exit(1)

    def _create_parser(self) -> argparse.ArgumentParser:
        """Create the main argument parser."""
        parser = argparse.ArgumentParser(
            description="Backtesting CLI for NSE markets",
            formatter_class=argparse.RawDescriptionHelpFormatter
        )

        subparsers = parser.add_subparsers(dest='command', help='Available commands')

        # Run command
        run_parser = subparsers.add_parser('run', help='Run a single backtest')
        run_parser.add_argument('--strategy', required=True, help='Strategy name')
        run_parser.add_argument('--symbols', required=True, nargs='+', help='Trading symbols')
        run_parser.add_argument('--from-date', required=True, help='Start date (YYYY-MM-DD)')
        run_parser.add_argument('--to-date', required=True, help='End date (YYYY-MM-DD)')
        run_parser.add_argument('--parameters', type=json.loads, default={}, help='Strategy parameters as JSON')
        run_parser.add_argument('--output', help='Output directory for reports')
        run_parser.add_argument('--config', help='Configuration file')

        # Batch command
        batch_parser = subparsers.add_parser('batch', help='Run batch backtests')
        batch_parser.add_argument('--strategy', required=True, help='Strategy name')
        batch_parser.add_argument('--symbols-file', required=True, help='File with list of symbols')
        batch_parser.add_argument('--from-date', required=True, help='Start date (YYYY-MM-DD)')
        batch_parser.add_argument('--to-date', required=True, help='End date (YYYY-MM-DD)')
        batch_parser.add_argument('--parameters', type=json.loads, default={}, help='Strategy parameters as JSON')
        batch_parser.add_argument('--workers', type=int, default=4, help='Number of parallel workers')
        batch_parser.add_argument('--output', help='Output directory for reports')
        batch_parser.add_argument('--batch-size', type=int, default=10, help='Symbols per batch')

        # Walk-forward command
        wf_parser = subparsers.add_parser('walk-forward', help='Run walk-forward analysis')
        wf_parser.add_argument('--strategy', required=True, help='Strategy name')
        wf_parser.add_argument('--symbols', required=True, nargs='+', help='Trading symbols')
        wf_parser.add_argument('--from-date', required=True, help='Start date (YYYY-MM-DD)')
        wf_parser.add_argument('--to-date', required=True, help='End date (YYYY-MM-DD)')
        wf_parser.add_argument('--param-ranges', type=json.loads, required=True, help='Parameter ranges as JSON')
        wf_parser.add_argument('--train-days', type=int, default=252, help='Training period days')
        wf_parser.add_argument('--test-days', type=int, default=63, help='Test period days')
        wf_parser.add_argument('--step-days', type=int, default=21, help='Step size days')
        wf_parser.add_argument('--output', help='Output directory for reports')

        # Data commands
        data_parser = subparsers.add_parser('data', help='Data management commands')
        data_subparsers = data_parser.add_subparsers(dest='data_command')

        # Data ingest
        ingest_parser = data_subparsers.add_parser('ingest', help='Ingest data from CSV')
        ingest_parser.add_argument('--file', required=True, help='CSV file to ingest')
        ingest_parser.add_argument('--symbol', required=True, help='Symbol name')
        ingest_parser.add_argument('--timeframe', default='1d', help='Timeframe')

        # Data list
        list_parser = data_subparsers.add_parser('list', help='List available data')
        list_parser.add_argument('--symbol', help='Filter by symbol')
        list_parser.add_argument('--from-date', help='Filter from date')
        list_parser.add_argument('--to-date', help='Filter to date')

        # Data validate
        validate_parser = data_subparsers.add_parser('validate', help='Validate data quality')
        validate_parser.add_argument('--symbol', required=True, help='Symbol to validate')
        validate_parser.add_argument('--from-date', help='Start date')
        validate_parser.add_argument('--to-date', help='End date')

        return parser

    def _cmd_run(self, args: argparse.Namespace) -> None:
        """Run a single backtest."""
        print(f"Running backtest for strategy: {args.strategy}")
        print(f"Symbols: {', '.join(args.symbols)}")
        print(f"Period: {args.from_date} to {args.to_date}")

        # Parse dates
        start_date = date.fromisoformat(args.from_date)
        end_date = date.fromisoformat(args.to_date)

        # Create output directory
        output_dir = Path(args.output) if args.output else Path(f"backtest_results_{int(time.time())}")
        output_dir.mkdir(exist_ok=True)

        # Run backtest
        report = self._run_single_backtest(
            strategy_name=args.strategy,
            parameters=args.parameters,
            symbols=args.symbols,
            start_date=start_date,
            end_date=end_date
        )

        # Generate reports
        reporter = BacktestReporter(report.portfolio_accounting)
        backtest_report = reporter.generate_report(
            run_id=f"cli_run_{int(time.time())}",
            strategy_name=args.strategy,
            symbols=args.symbols,
            start_date=start_date,
            end_date=end_date,
            parameters=args.parameters
        )

        # Export reports
        json_file = output_dir / "report.json"
        csv_trades_file = output_dir / "trades.csv"
        csv_equity_file = output_dir / "equity.csv"
        html_file = output_dir / "report.html"

        reporter.export_json(backtest_report, str(json_file))
        reporter.export_csv_trades(backtest_report, str(csv_trades_file))
        reporter.export_csv_equity(backtest_report, str(csv_equity_file))
        reporter.generate_html_report(backtest_report, str(html_file))

        # Print summary
        print("\nBacktest completed successfully!")
        print(f"Total Return: {backtest_report.metrics.total_return_pct:.2f}%")
        print(f"Sharpe Ratio: {backtest_report.metrics.sharpe_ratio:.2f}")
        print(f"Win Rate: {backtest_report.metrics.win_rate_pct:.1f}%")
        print(f"Total Trades: {backtest_report.metrics.total_trades}")
        print(f"\nReports saved to: {output_dir}")

    def _cmd_batch(self, args: argparse.Namespace) -> None:
        """Run batch backtests with multiprocessing."""
        print(f"Running batch backtest for strategy: {args.strategy}")

        # Load symbols from file
        with open(args.symbols_file, 'r') as f:
            symbols = [line.strip() for line in f if line.strip()]

        print(f"Loaded {len(symbols)} symbols from {args.symbols_file}")

        # Parse dates
        start_date = date.fromisoformat(args.from_date)
        end_date = date.fromisoformat(args.to_date)

        # Create output directory
        output_dir = Path(args.output) if args.output else Path(f"batch_results_{int(time.time())}")
        output_dir.mkdir(exist_ok=True)

        # Run parallel batch processing
        start_time = time.time()

        # Use ProcessPoolExecutor for symbol-level parallelism
        with concurrent.futures.ProcessPoolExecutor(max_workers=args.workers) as executor:
            # Submit jobs for each symbol
            future_to_symbol = {
                executor.submit(self._run_single_backtest_parallel,
                              args.strategy, args.parameters, [symbol], start_date, end_date): symbol
                for symbol in symbols
            }

            results = []
            for future in concurrent.futures.as_completed(future_to_symbol):
                symbol = future_to_symbol[future]
                try:
                    result = future.result()
                    results.append(result)
                except Exception as exc:
                    results.append({
                        'symbol': symbol,
                        'error': str(exc),
                        'report': None
                    })

        total_time = time.time() - start_time

        # Process results
        successful = [r for r in results if not r.get('error')]
        failed = [r for r in results if r.get('error')]

        print(f"\nBatch completed in {total_time:.2f} seconds")
        print(f"Successful: {len(successful)}/{len(results)}")

        if failed:
            print(f"Failed: {len(failed)}")
            for failure in failed[:5]:  # Show first 5 failures
                print(f"  - {failure['symbol']}: {failure['error']}")

        # Generate summary report
        self._generate_batch_summary(results, output_dir, args)

        print(f"\nResults saved to: {output_dir}")

    def _run_single_backtest_parallel(self, strategy_name: str, parameters: Dict[str, Any],
                                    symbols: List[str], start_date: date, end_date: date) -> Dict[str, Any]:
        """
        Run a single backtest in a separate process.

        This ensures RiskEngine state isolation per process.
        """
        try:
            # Create isolated risk engine instance per process
            from core.risk.risk_engine import RiskEngine
            risk_engine = RiskEngine(capital=100000.0)

            # Run backtest logic here (placeholder)
            report = self._run_single_backtest(strategy_name, parameters, symbols, start_date, end_date)

            return {
                'symbol': symbols[0],
                'error': None,
                'report': report
            }
        except Exception as e:
            return {
                'symbol': symbols[0],
                'error': str(e),
                'report': None
            }

    def _cmd_walk_forward(self, args: argparse.Namespace) -> None:
        """Run walk-forward analysis."""
        print(f"Running walk-forward analysis for strategy: {args.strategy}")

        # Parse dates
        start_date = date.fromisoformat(args.from_date)
        end_date = date.fromisoformat(args.to_date)

        # Create parameter grid
        grid_search = ParameterGridSearch(args.param_ranges)
        parameter_sets = grid_search.generate_parameter_sets()

        print(f"Testing {len(parameter_sets)} parameter combinations")

        # Create output directory
        output_dir = Path(args.output) if args.output else Path(f"wf_results_{int(time.time())}")
        output_dir.mkdir(exist_ok=True)

        # Create walk-forward analyzer
        analyzer = WalkForwardAnalyzer(
            strategy_runner=self._run_single_backtest,
            initial_train_days=args.train_days,
            test_days=args.test_days,
            step_days=args.step_days
        )

        # Run analysis
        report = analyzer.run_walk_forward(
            parameter_sets,
            args.symbols,
            start_date,
            end_date,
            analysis_name=f"wf_{args.strategy}_{int(time.time())}"
        )

        # Export results
        from .walk_forward import export_validation_report
        json_file = output_dir / "validation_report.json"
        export_validation_report(report, str(json_file))

        # Print summary
        print("\nWalk-forward analysis completed!")
        print(f"Total parameter sets: {len(report.parameter_sets)}")
        print(f"Total windows: {report.total_windows}")
        print(f"Average OOS performance: {report.avg_oos_performance:.3f}")
        print(f"Average overfitting score: {report.avg_overfitting_score:.3f}")

        if report.best_parameter_set:
            best = report.best_parameter_set
            print(f"\nBest parameter set: {best.parameter_set.name}")
            print(f"Robustness score: {best.robustness_score:.3f}")
            print(f"Avg OOS return: {best.avg_test_return:.2f}%")
            print(f"Avg IS return: {best.avg_train_return:.2f}%")

        print(f"\nResults saved to: {output_dir}")

    def _cmd_data(self, args: argparse.Namespace) -> None:
        """Handle data management commands."""
        if args.data_command == 'ingest':
            self._cmd_data_ingest(args)
        elif args.data_command == 'list':
            self._cmd_data_list(args)
        elif args.data_command == 'validate':
            self._cmd_data_validate(args)
        else:
            print(f"Unknown data command: {args.data_command}")

    def _cmd_data_ingest(self, args: argparse.Namespace) -> None:
        """Ingest data from CSV file."""
        from .data_ingestion import DataIngestion

        print(f"Ingesting data from {args.file} for symbol {args.symbol}")

        ingestor = DataIngestion()
        result = ingestor.ingest_csv(args.file, args.symbol, args.timeframe)

        print(f"Ingested {result.records_processed} records")
        if result.errors:
            print(f"Errors encountered: {len(result.errors)}")
            for error in result.errors[:5]:
                print(f"  - {error}")

    def _cmd_data_list(self, args: argparse.Namespace) -> None:
        """List available data."""
        # This would query the data storage and display available data
        print("Available data:")
        print("(Data listing not yet implemented)")

    def _cmd_data_validate(self, args: argparse.Namespace) -> None:
        """Validate data quality."""
        # This would run data quality checks
        print(f"Validating data for {args.symbol}")
        print("(Data validation not yet implemented)")

    def _run_single_backtest(self, strategy_name: str, parameters: Dict[str, Any],
                           symbols: List[str], start_date: date, end_date: date) -> Any:
        """
        Run a single backtest.

        This is a placeholder - in the real implementation, this would:
        1. Load market data for the symbols and date range
        2. Create and initialize the strategy
        3. Run the backtest engine
        4. Return the results

        For now, returns a mock result.
        """
        # Mock implementation - replace with actual backtest logic
        from .portfolio_accounting import PortfolioAccounting
        from .reporting import BacktestReport, PerformanceMetrics

        portfolio = PortfolioAccounting(Decimal('100000'))

        # Mock some trades
        for i in range(10):
            from .portfolio_accounting import TradeRecord
            from datetime import datetime
            trade = TradeRecord(
                symbol=symbols[0],
                side="BUY",
                quantity=100,
                entry_price=Decimal('2500'),
                exit_price=Decimal('2520'),
                entry_time=datetime.now(),
                exit_time=datetime.now(),
                realized_pnl=Decimal('2000'),
                fees=Decimal('25'),
                tags=[]
            )
            portfolio.record_trade(trade)

        # Create mock report
        report = BacktestReport(
            run_id=f"mock_{strategy_name}",
            strategy_name=strategy_name,
            symbols=symbols,
            start_date=start_date,
            end_date=end_date,
            initial_capital=100000.0,
            metrics=PerformanceMetrics(
                total_return_pct=15.0,
                sharpe_ratio=1.8,
                win_rate_pct=65.0,
                total_trades=10
            )
        )

        # Attach portfolio for reporting
        report.portfolio_accounting = portfolio

        return report

    def _generate_batch_summary(self, results: List, output_dir: Path, job: BatchJob) -> None:
        """Generate batch summary report."""
        successful = [r for r in results if not r.error]
        failed = [r for r in results if r.error]

        summary = {
            'batch_id': f"batch_{int(time.time())}",
            'strategy': args.strategy,
            'total_symbols': len(results),
            'successful': len(successful),
            'failed': len(failed),
            'parameters': args.parameters,
            'date_range': {
                'start': args.from_date,
                'end': args.to_date
            },
            'results': []
        }

        # Add individual results
        for result in successful:
            if result.report:
                summary['results'].append({
                    'symbol': result.symbol,
                    'total_return_pct': result.report.metrics.total_return_pct,
                    'sharpe_ratio': result.report.metrics.sharpe_ratio,
                    'win_rate_pct': result.report.metrics.win_rate_pct,
                    'total_trades': result.report.metrics.total_trades,
                    'execution_time_seconds': result.performance.execution_time_seconds
                })

        # Add failures
        summary['failures'] = [
            {'symbol': r.symbol, 'error': r.error} for r in failed
        ]

        # Save summary
        summary_file = output_dir / "batch_summary.json"
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)


def main():
    """CLI entry point."""
    cli = BacktestCLI()
    cli.run()


if __name__ == "__main__":
    main()
