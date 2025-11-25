#!/usr/bin/env python3
"""
Standalone realtime data ingestion script.
Connects to websocket providers and ingests live market data.
"""

import asyncio
import argparse
import os
import signal
import sys
from pathlib import Path
from typing import List

# Add the project root to the Python path
ROOT_PATH = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT_PATH))

from market_data_ingestion.core.storage import DataStorage
from market_data_ingestion.adapters.kite_ws import KiteWebSocketAdapter
from market_data_ingestion.adapters.mock_ws import MockWebSocketServer
from market_data_ingestion.core.aggregator import TickAggregator
from market_data_ingestion.src.logging_config import setup_logging
import logging
import tenacity

logger = logging.getLogger(__name__)

class RealtimeIngestionManager:
    """Manages realtime data ingestion with graceful shutdown."""

    def __init__(self, symbols: List[str], provider: str, db_url: str):
        self.symbols = symbols
        self.provider = provider
        self.db_url = db_url
        self.storage = None
        self.aggregator = None
        self.adapter = None
        self.aggregator_task = None
        self.mock_server = None
        self.running = False

    async def start(self):
        """Start realtime ingestion."""
        self.running = True

        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

        try:
            # Initialize storage
            self.storage = DataStorage(self.db_url)
            await self.storage.connect()
            await self.storage.create_tables()

            # Initialize aggregator
            self.aggregator = TickAggregator()

            # Start aggregator task
            self.aggregator_task = asyncio.create_task(self.aggregator.run())

            # Choose adapter based on provider
            if self.provider == "kite_ws":
                config = {
                    "api_key": os.getenv("KITE_API_KEY", ""),
                    "api_secret": os.getenv("KITE_API_SECRET", ""),
                    "websocket_url": os.getenv("KITE_WS_URL", "ws://localhost:8765"),
                    "reconnect_interval": 5,
                    "heartbeat_interval": 30
                }
                self.adapter = KiteWebSocketAdapter(config)
            elif self.provider == "mock":
                # Start mock server
                self.mock_server = MockWebSocketServer()
                mock_task = asyncio.create_task(self.mock_server.start())

                # Use kite adapter with mock URL
                config = {
                    "api_key": "mock",
                    "api_secret": "mock",
                    "websocket_url": "ws://localhost:8765",
                    "reconnect_interval": 5,
                    "heartbeat_interval": 30
                }
                self.adapter = KiteWebSocketAdapter(config)

                # Wait a bit for mock server to start
                await asyncio.sleep(2)
            else:
                raise ValueError(f"Unsupported provider: {self.provider}")

            # Connect to websocket and start receiving data
            async with self.adapter:
                await self.adapter.realtime_connect(self.symbols)

        except Exception as e:
            logger.error(f"Error in realtime ingestion: {e}")
            raise
        finally:
            await self.stop()

    async def stop(self):
        """Stop realtime ingestion gracefully."""
        if not self.running:
            return

        self.running = False
        logger.info("Stopping realtime ingestion...")

        # Stop aggregator
        if self.aggregator_task:
            self.aggregator_task.cancel()
            try:
                await self.aggregator_task
            except asyncio.CancelledError:
                pass

        # Flush any remaining candles
        if self.aggregator:
            await self.aggregator.flush_candles()

        # Stop mock server
        if self.mock_server:
            await self.mock_server.stop()

        # Disconnect storage
        if self.storage:
            await self.storage.disconnect()

        logger.info("Realtime ingestion stopped")

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        logger.info(f"Received signal {signum}, initiating shutdown...")
        asyncio.create_task(self.stop())

async def main():
    parser = argparse.ArgumentParser(description="Realtime data ingestion script")
    parser.add_argument(
        "--symbols",
        nargs="+",
        required=True,
        help="List of symbols to ingest in realtime"
    )
    parser.add_argument(
        "--provider",
        required=True,
        choices=["kite_ws", "mock"],
        help="Data provider to use"
    )
    parser.add_argument(
        "--db-url",
        help="Database URL",
        default=os.getenv("DATABASE_URL", "sqlite:///market_data.db")
    )

    args = parser.parse_args()

    # Setup logging
    setup_logging()
    logger.info(f"Starting realtime ingestion with symbols: {args.symbols}, provider: {args.provider}")

    try:
        # Initialize and start ingestion manager
        manager = RealtimeIngestionManager(args.symbols, args.provider, args.db_url)
        await manager.start()

    except KeyboardInterrupt:
        logger.info("Realtime ingestion interrupted by user")
    except Exception as e:
        logger.error(f"Realtime ingestion failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
