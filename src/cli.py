import asyncio
import argparse
import logging
import yaml
import os
from datetime import datetime, timedelta

from market_data_ingestion.core.storage import DataStorage
from market_data_ingestion.adapters.yfinance import YFinanceAdapter
from market_data_ingestion.adapters.alphavantage import AlphaVantageAdapter
from market_data_ingestion.adapters.kite_ws import KiteWebSocketAdapter
from market_data_ingestion.core.aggregator import TickAggregator
from market_data_ingestion.core.fetcher_manager import FetcherManager

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

async def backfill(args):
    """
    Backfills historical data for specified symbols.
    """
    logging.info(f"Running backfill with symbols: {args.symbols}, period: {args.period}, interval: {args.interval}")

    # Load configuration
    config_path = os.path.join(os.path.dirname(__file__), '..', 'market_data_ingestion', 'config', 'config.example.yaml')
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)

    # Initialize storage
    storage = DataStorage(config['database']['db_path'])
    await storage.connect()
    await storage.create_tables()

    # Initialize fetcher manager
    fetcher_manager = FetcherManager()

    # Determine end date (today)
    end_date = datetime.now().strftime('%Y-%m-%d')

    # Calculate start date based on period
    period_days = int(args.period.rstrip('d'))
    start_date = (datetime.now() - timedelta(days=period_days)).strftime('%Y-%m-%d')

    # Fetch data for each symbol
    for symbol in args.symbols:
        logging.info(f"Backfilling {symbol} from {start_date} to {end_date} with interval {args.interval}")

        # Choose adapter based on provider (default to yfinance)
        adapter = YFinanceAdapter(config['providers']['yfinance'])

        try:
            data = await adapter.fetch_historical_data(symbol, start_date, end_date, args.interval)
            logging.info(f"Fetched {len(data)} records for {symbol}")

            # Store data
            for candle in data:
                await storage.insert_candle(candle)

        except Exception as e:
            logging.error(f"Error backfilling {symbol}: {e}")

    await storage.disconnect()
    logging.info("Backfill completed")

async def realtime(args):
    """
    Starts realtime data ingestion for specified symbols.
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

async def migrate(args):
    """
    Runs database migrations.
    """
    logging.info("Running database migrations")

    # Load configuration
    config_path = os.path.join(os.path.dirname(__file__), '..', 'market_data_ingestion', 'config', 'config.example.yaml')
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)

    # Initialize storage
    storage = DataStorage(config['database']['db_path'])
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

async def main():
    parser = argparse.ArgumentParser(description="Market data ingestion CLI")
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # Backfill command
    backfill_parser = subparsers.add_parser("backfill", help="Backfill historical data")
    backfill_parser.add_argument("--symbols", nargs="+", required=True, help="List of symbols to backfill")
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

    args = parser.parse_args()

    if args.command:
        await args.func(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    asyncio.run(main())
