"""
Realtime data ingestion pipeline.
"""

import asyncio
import logging
from typing import Dict, List, Optional

from ..adapters.base import ProviderAdapter
from ..normalization.normalizer import DataNormalizer
from ..storage.writer import DataWriter

logger = logging.getLogger(__name__)


class RealtimePipeline:
    """Realtime data ingestion pipeline."""

    def __init__(self, adapter: ProviderAdapter, writer: DataWriter,
                 normalizer: DataNormalizer, batch_size: int = 100,
                 flush_interval: float = 5.0):
        self.adapter = adapter
        self.writer = writer
        self.normalizer = normalizer
        self.batch_size = batch_size
        self.flush_interval = flush_interval
        self.running = False
        self.tasks: List[asyncio.Task] = []

    async def start_trades_stream(self, symbol: str):
        """Start streaming trades for a symbol."""
        logger.info(f"Starting trades stream for {symbol}")

        buffer = []
        last_flush = asyncio.get_event_loop().time()

        try:
            async for raw_trade in self.adapter.stream_trades(symbol):
                # Normalize trade
                trade = self.normalizer.normalize_trade(raw_trade)
                if trade:
                    buffer.append(trade)

                # Flush buffer if full or time interval reached
                current_time = asyncio.get_event_loop().time()
                if (len(buffer) >= self.batch_size or
                    current_time - last_flush >= self.flush_interval):
                    if buffer:
                        count = await self.writer.write_trades(buffer)
                        logger.debug(f"Flushed {count} trades for {symbol}")
                        buffer.clear()
                        last_flush = current_time

        except Exception as e:
            logger.error(f"Error in trades stream for {symbol}: {e}")
            raise

    async def start_quotes_stream(self, symbol: str):
        """Start streaming quotes for a symbol."""
        logger.info(f"Starting quotes stream for {symbol}")

        buffer = []
        last_flush = asyncio.get_event_loop().time()

        try:
            async for raw_quote in self.adapter.stream_quotes(symbol):
                # Normalize quote
                quote = self.normalizer.normalize_quote(raw_quote)
                if quote:
                    buffer.append(quote)

                # Flush buffer (quotes are typically single records)
                current_time = asyncio.get_event_loop().time()
                if (len(buffer) >= self.batch_size or
                    current_time - last_flush >= self.flush_interval):
                    if buffer:
                        count = await self.writer.write_quotes(buffer)
                        logger.debug(f"Flushed {count} quotes for {symbol}")
                        buffer.clear()
                        last_flush = current_time

        except Exception as e:
            logger.error(f"Error in quotes stream for {symbol}: {e}")
            raise

    async def start(self, symbols: List[str], include_quotes: bool = False):
        """Start the realtime pipeline for multiple symbols."""
        if self.running:
            logger.warning("Pipeline already running")
            return

        self.running = True
        logger.info(f"Starting realtime pipeline for symbols: {symbols}")

        try:
            # Create tasks for each symbol
            for symbol in symbols:
                task = asyncio.create_task(self.start_trades_stream(symbol))
                self.tasks.append(task)

                if include_quotes:
                    task = asyncio.create_task(self.start_quotes_stream(symbol))
                    self.tasks.append(task)

            # Wait for all tasks
            await asyncio.gather(*self.tasks, return_exceptions=True)

        except Exception as e:
            logger.error(f"Error in realtime pipeline: {e}")
            raise
        finally:
            self.running = False

    async def stop(self):
        """Stop the realtime pipeline."""
        if not self.running:
            return

        logger.info("Stopping realtime pipeline")

        # Cancel all tasks
        for task in self.tasks:
            if not task.done():
                task.cancel()

        # Wait for tasks to complete
        await asyncio.gather(*self.tasks, return_exceptions=True)
        self.tasks.clear()
        self.running = False
