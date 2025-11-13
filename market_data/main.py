"""
Main entry point for the market data ingestion system.
"""

import asyncio
import logging
import signal
import sys
from typing import List

import yaml

from .adapters.polygon import PolygonAdapter
from .adapters.binance import BinanceAdapter
from .config import load_config
from .normalization.normalizer import DataNormalizer
from .pipelines.realtime import RealtimePipeline
from .storage.writer import DataWriter
from .monitoring.health import HealthChecker
from .monitoring.metrics import metrics

logger = logging.getLogger(__name__)


class MarketDataIngestion:
    """Main market data ingestion service."""

    def __init__(self, config_path: str = "market_data/config/default.yaml"):
        self.config = load_config(config_path)
        self.writer = DataWriter(
            dsn=self.config['database']['dsn'],
            min_connections=self.config['database']['min_connections'],
            max_connections=self.config['database']['max_connections']
        )
        self.adapters = {}
        self.pipelines = {}
        self.health_checker = HealthChecker(
            self.writer,
            port=self.config['monitoring']['prometheus_port']
        )
        self.running = False

    async def initialize(self):
        """Initialize the ingestion service."""
        logger.info("Initializing market data ingestion service")

        # Connect to database
        await self.writer.connect()

        # Initialize adapters
        await self._initialize_adapters()

        # Start health checker
        if self.config['monitoring']['metrics_enabled']:
            await self.health_checker.start()

        logger.info("Market data ingestion service initialized")

    async def _initialize_adapters(self):
        """Initialize provider adapters."""
        for provider_name, provider_config in self.config['providers'].items():
            if not provider_config.get('is_active', True):
                continue

            if provider_name == 'polygon':
                adapter = PolygonAdapter(provider_config)
            elif provider_name == 'binance':
                adapter = BinanceAdapter(provider_config)
            else:
                logger.warning(f"Unknown provider: {provider_name}")
                continue

            # Initialize adapter session
            async with adapter:
                self.adapters[provider_name] = adapter

            logger.info(f"Initialized adapter for {provider_name}")

    async def start_realtime_ingestion(self, symbols: List[str] = None):
        """Start realtime data ingestion."""
        if symbols is None:
            symbols = [inst['symbol'] for inst in self.config['instruments']]

        logger.info(f"Starting realtime ingestion for symbols: {symbols}")

        # Start pipelines for each provider
        tasks = []
        for provider_name, adapter in self.adapters.items():
            provider_symbols = [
                symbol for symbol in symbols
                if any(inst['symbol'] == symbol and inst.get('provider') == provider_name
                      for inst in self.config['instruments'])
            ]

            if not provider_symbols:
                continue

            # Get provider and instrument IDs
            provider_id = await self.writer.get_provider_id(provider_name)
            if not provider_id:
                logger.error(f"Provider {provider_name} not found in database")
                continue

            # Create normalizer
            normalizer = DataNormalizer(provider_id, 1)  # TODO: Get instrument ID

            # Create pipeline
            pipeline = RealtimePipeline(
                adapter=adapter,
                writer=self.writer,
                normalizer=normalizer,
                batch_size=self.config['pipelines']['realtime']['batch_size'],
                flush_interval=self.config['pipelines']['realtime']['flush_interval_seconds']
            )

            # Start pipeline
            task = asyncio.create_task(
                pipeline.start(provider_symbols, include_quotes=True)
            )
            tasks.append(task)
            self.pipelines[provider_name] = pipeline

        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    async def shutdown(self):
        """Shutdown the ingestion service."""
        logger.info("Shutting down market data ingestion service")

        # Stop pipelines
        for pipeline in self.pipelines.values():
            await pipeline.stop()

        # Stop health checker
        await self.health_checker.stop()

        # Disconnect from database
        await self.writer.disconnect()

        logger.info("Market data ingestion service shut down")

    async def run(self):
        """Run the ingestion service."""
        self.running = True

        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}, shutting down")
            self.running = False

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        try:
            await self.initialize()

            # Start realtime ingestion
            if self.config['pipelines']['realtime']['enabled']:
                await self.start_realtime_ingestion()

        except Exception as e:
            logger.error(f"Error in ingestion service: {e}")
            raise
        finally:
            await self.shutdown()


async def main():
    """Main entry point."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    service = MarketDataIngestion()
    await service.run()


if __name__ == "__main__":
    asyncio.run(main())
