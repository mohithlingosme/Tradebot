import asyncio
import argparse
import contextlib
import logging
import os
from typing import Any, Dict
import signal

from market_data_ingestion.core.storage import DataStorage
from market_data_ingestion.adapters.yfinance import YFinanceAdapter
from market_data_ingestion.adapters.alphavantage import AlphaVantageAdapter
from market_data_ingestion.adapters.kite_ws import KiteWebSocketAdapter
from market_data_ingestion.adapters.mock_ws import MockWebSocketServer
from market_data_ingestion.core.aggregator import TickAggregator
from market_data_ingestion.core.fetcher_manager import FetcherManager
from market_data_ingestion.core.scheduler import AutoRefreshScheduler
from market_data_ingestion.core.tasks.backfill_runner import BackfillRunner, BackfillConfig
from market_data_ingestion.src.logging_config import setup_logging
from market_data_ingestion.src.settings import settings
import tenacity
import csv

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
    if not args.symbols and not getattr(args, "csv_file", None):
        raise ValueError("No symbols provided")

    symbols = args.symbols or []
    if getattr(args, "csv_file", None):
        symbols += load_symbols_from_csv(args.csv_file)

    backfill_config = BackfillConfig(
        symbols=symbols,
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

    # Initialize storage
    storage = DataStorage(settings.database_url)
    await storage.connect()
    await storage.create_tables()

    # Initialize aggregator
    aggregator = TickAggregator()

    # Choose adapter based on provider
    adapter_config = settings.provider_config(args.provider)
    adapter = None

    if args.provider == "mock":
        mock_server = MockWebSocketServer()
        mock_task = asyncio.create_task(mock_server.start())
        if adapter_config is None:
            adapter_config = settings.provider_config("mock")
        if adapter_config is None:
            logging.error("Mock provider configuration is missing")
            return
        adapter = KiteWebSocketAdapter(adapter_config.copy())
        await asyncio.sleep(2)
    elif adapter_config:
        adapter = KiteWebSocketAdapter(adapter_config.copy())
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

    # Initialize storage with database URL
    db_url = os.getenv('DATABASE_URL', settings.database_url)
    storage = DataStorage(db_url)
    await storage.connect()
    await storage.create_tables()

    await storage.disconnect()
    logging.info("Database migrations completed")

async def run_worker(args):
    """
    Orchestrate realtime streaming + scheduled refresh jobs.
    """
    logging.info("Running worker process")
    stop_event = asyncio.Event()
    loop = asyncio.get_running_loop()
    try:
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, stop_event.set)
    except NotImplementedError:
        # Windows event loop may not support add_signal_handler.
        pass

    storage = DataStorage(settings.database_url)
    await storage.connect()
    await storage.create_tables()

    aggregator = TickAggregator()
    aggregator_task = asyncio.create_task(aggregator.run())
    scheduler = AutoRefreshScheduler()
    scheduler_task = asyncio.create_task(scheduler.run_forever())

    async def persist_tick(provider_name: str, tick):
        payload = tick.to_dict()
        payload["provider"] = provider_name
        await storage.insert_tick(payload)
        metrics_collector.record_ingestion_request(provider_name, payload["symbol"], "success")
        metrics_collector.record_data_points_ingested(provider_name, "ticks", 1)
        await aggregator.aggregate_tick(
            {
                "symbol": payload["symbol"],
                "ts_utc": payload["ts_utc"],
                "price": payload["price"],
                "qty": payload["volume"],
            }
        )

    def symbols_for_provider(provider_name: str, provider_cfg: Dict[str, Any]) -> list[str]:
        configured = [
            inst["symbol"]
            for inst in settings.instruments
            if inst.get("provider") == provider_name and inst.get("symbol")
        ]
        extra = provider_cfg.get("symbols") or []
        configured.extend(extra)
        return sorted({symbol for symbol in configured if symbol})

    stream_tasks: list[asyncio.Task] = []
    mock_server = None

    if settings.provider_configs.get("mock", {}).get("is_active"):
        mock_server = MockWebSocketServer()
        stream_tasks.append(asyncio.create_task(mock_server.start()))

    for provider_name, provider_cfg in settings.provider_configs.items():
        if not provider_cfg.get("is_active"):
            continue
        if "websocket_url" not in provider_cfg:
            continue

        async def run_stream(name=provider_name, cfg=provider_cfg.copy()):
            adapter = KiteWebSocketAdapter(cfg)

            async def on_tick(tick):
                await persist_tick(name, tick)

            adapter.set_tick_handler(on_tick)
            provider_symbols = symbols_for_provider(name, cfg)
            if not provider_symbols:
                logging.warning("No symbols configured for provider %s; skipping stream.", name)
                return
            await adapter.realtime_connect(provider_symbols)

        stream_tasks.append(asyncio.create_task(run_stream()))

    metrics_collector.update_active_connections("websocket", len(stream_tasks))

    try:
        await stop_event.wait()
    finally:
        for task in stream_tasks:
            task.cancel()
        if mock_server:
            await mock_server.stop()
        scheduler_task.cancel()
        aggregator_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await asyncio.gather(*stream_tasks, return_exceptions=True)
            await scheduler_task
            await aggregator_task
        await storage.disconnect()
        logging.info("Worker shut down cleanly")

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


def load_symbols_from_csv(csv_path: str) -> list[str]:
    """Load a symbol column from a CSV file and return list of symbols.

    Parameters
    ----------
    csv_path: str
        Path to CSV file with a 'symbol' column.

    Returns
    -------
    list[str]
        List of symbols read from the CSV.
    """
    if not os.path.exists(csv_path):
        raise FileNotFoundError(csv_path)
    symbols = []
    with open(csv_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            symbol = row.get('symbol')
            if symbol:
                symbols.append(symbol.strip())
    return symbols

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
