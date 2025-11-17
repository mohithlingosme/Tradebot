import asyncio
import argparse
import logging
import yaml
import os

from market_data_ingestion.core.storage import DataStorage
from market_data_ingestion.adapters.yfinance import YFinanceAdapter
from market_data_ingestion.adapters.alphavantage import AlphaVantageAdapter
from market_data_ingestion.adapters.kite_ws import KiteWebSocketAdapter
from market_data_ingestion.core.aggregator import TickAggregator
from market_data_ingestion.core.fetcher_manager import FetcherManager
from market_data_ingestion.core.scheduler import AutoRefreshScheduler
from market_data_ingestion.core.tasks.backfill_runner import BackfillRunner, BackfillConfig
from market_data_ingestion.src.logging_config import setup_logging
import tenacity

# Set up logging
setup_logging()
logger = logging.getLogger(__name__)

@tenacity.retry(
    stop=tenacity.stop_after_attempt(3),
    wait=tenacity.wait_exponential(multiplier=1, min=4, max=10),
    retry=tenacity.retry_if_exception_type(Exception),
    before_sleep=tenacity.before_sleep_log(logger, logging.WARNING)
)
async def backfill(args):
    """
    Backfills historical data for specified symbols.
    Supports CSV file input and direct symbol list.
    """
    logging.info(f"Running backfill with symbols={args.symbols} period={args.period} interval={args.interval}")
    backfill_config = BackfillConfig(
        symbols=args.symbols or [],
        period=args.period,
        interval=args.interval,
        csv_file=getattr(args, "csv_file", None),
    )
    async with BackfillRunner() as runner:
        processed = await runner.run(backfill_config)
    logging.info("Backfill completed. Processed %s symbols", processed)

@tenacity.retry(
    stop=tenacity.stop_after_attempt(3),
    wait=tenacity.wait_exponential(multiplier=1, min=4, max=10),
    retry=tenacity.retry_if_exception_type(Exception),
    before_sleep=tenacity.before_sleep_log(logger, logging.WARNING)
)
async def realtime(args):
    """
    Starts realtime data ingestion for specified symbols.
    Enhanced with better error handling and graceful shutdown.
    """
    logging.info(f"Running realtime ingestion with symbols: {args.symbols}, provider: {args.provider}")

    # Load configuration
    config_path = os.path.join(os.path.dirname(__file__), '..', 'market_data_ingestion', 'config', 'config.example.yaml')
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)

    # Initialize storage
    storage = DataStorage(config['database']['db_path'])
    await storage.connect()
    await storage.create_tables()

    # Initialize aggregator
    aggregator = TickAggregator()

    # Choose adapter based on provider
    if args.provider == "kite_ws":
        adapter_config = config['providers']['kite_ws']
        adapter = KiteWebSocketAdapter(adapter_config)
    elif args.provider == "mock":
        # For mock, use kite_ws adapter with mock URL
        adapter_config = config['providers']['kite_ws'].copy()
        adapter_config['websocket_url'] = "ws://localhost:8765"
        adapter = KiteWebSocketAdapter(adapter_config)
    else:
        logging.error(f"Unsupported provider: {args.provider}")
        return

    # Start aggregator task
    aggregator_task = asyncio.create_task(aggregator.run())

    # Connect to websocket and start receiving data
    try:
        async with adapter:
            await adapter.realtime_connect(args.symbols)
    except KeyboardInterrupt:
        logging.info("Realtime ingestion interrupted by user")
    except Exception as e:
        logging.error(f"Error in realtime ingestion: {e}")
        raise
    finally:
        # Stop aggregator
        aggregator_task.cancel()
        try:
            await aggregator_task
        except asyncio.CancelledError:
            pass

        # Flush any remaining candles
        await aggregator.flush_candles()

        await storage.disconnect()
        logging.info("Realtime ingestion stopped")

@tenacity.retry(
    stop=tenacity.stop_after_attempt(3),
    wait=tenacity.wait_exponential(multiplier=1, min=4, max=10),
    retry=tenacity.retry_if_exception_type(Exception),
    before_sleep=tenacity.before_sleep_log(logger, logging.WARNING)
)
async def migrate(args):
    """
    Runs database migrations.
    Supports both SQLite and PostgreSQL.
    """
    logging.info("Running database migrations")

    # Load configuration
    config_path = os.path.join(os.path.dirname(__file__), '..', 'market_data_ingestion', 'config', 'config.example.yaml')
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)

    # Initialize storage with database URL
    db_url = os.getenv('DATABASE_URL', config['database']['db_path'])
    storage = DataStorage(db_url)
    await storage.connect()
    await storage.create_tables()

    await storage.disconnect()
    logging.info("Database migrations completed")

async def run_worker(args):
    """
    Runs a worker process.
    """
    logging.info("Running worker process")
    # TODO: Implement worker process logic here
    pass

async def mock_server(args):
    """
    Starts the mock WebSocket server.
    """
    logging.info("Starting mock WebSocket server")
    from market_data_ingestion.adapters.mock_ws import MockWebSocketServer
    server = MockWebSocketServer()
    try:
        await server.start()
    except KeyboardInterrupt:
        await server.stop()

async def auto_refresh(args):
    """
    Runs the daily auto-refresh scheduler.
    """
    scheduler = AutoRefreshScheduler()
    if args.run_time:
        scheduler.settings.run_time = args.run_time
    if args.timezone:
        scheduler.settings.timezone = args.timezone
    if args.period:
        scheduler.settings.period = args.period
    if args.interval:
        scheduler.settings.interval = args.interval
    if args.symbols:
        scheduler.settings.symbols = args.symbols

    if getattr(args, "run_once", False):
        await scheduler.trigger_refresh()
    else:
        await scheduler.run_forever()

async def main():
    parser = argparse.ArgumentParser(description="Market data ingestion CLI")
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # Backfill command
    backfill_parser = subparsers.add_parser("backfill", help="Backfill historical data")
    backfill_parser.add_argument("--symbols", nargs="+", help="List of symbols to backfill")
    backfill_parser.add_argument("--csv-file", help="CSV file containing symbols to backfill")
    backfill_parser.add_argument("--period", required=True, help="Period to backfill (e.g., 7d, 30d)")
    backfill_parser.add_argument("--interval", required=True, help="Interval to backfill (e.g., 1m, 1h, 1d)")
    backfill_parser.set_defaults(func=backfill)

    # Realtime command
    realtime_parser = subparsers.add_parser("realtime", help="Start realtime data ingestion")
    realtime_parser.add_argument("--symbols", nargs="+", required=True, help="List of symbols to ingest in realtime")
    realtime_parser.add_argument("--provider", required=True, help="Data provider to use (e.g., mock, kite)")
    realtime_parser.set_defaults(func=realtime)

    # Migrate command
    migrate_parser = subparsers.add_parser("migrate", help="Run database migrations")
    migrate_parser.set_defaults(func=migrate)

    # Run worker command
    run_worker_parser = subparsers.add_parser("run-worker", help="Run a worker process")
    run_worker_parser.set_defaults(func=run_worker)

    # Mock server command
    mock_server_parser = subparsers.add_parser("mock-server", help="Start mock WebSocket server")
    mock_server_parser.set_defaults(func=mock_server)

    # Auto-refresh scheduler command
    auto_refresh_parser = subparsers.add_parser("auto-refresh", help="Run daily auto-refresh scheduler")
    auto_refresh_parser.add_argument("--run-once", action="store_true", help="Run refresh immediately and exit")
    auto_refresh_parser.add_argument("--run-time", help="HH:MM time the job should run (default from config)")
    auto_refresh_parser.add_argument("--timezone", help="Timezone identifier for scheduling (default from config)")
    auto_refresh_parser.add_argument("--period", help="Override backfill period, e.g., 7d")
    auto_refresh_parser.add_argument("--interval", help="Override backfill interval, e.g., 1h")
    auto_refresh_parser.add_argument("--symbols", nargs="+", help="Override symbols for the refresh run")
    auto_refresh_parser.set_defaults(func=auto_refresh)

    args = parser.parse_args()

    if args.command:
        await args.func(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    asyncio.run(main())
