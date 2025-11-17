import asyncio
import logging
from collections import defaultdict
from typing import Dict, Any

import pandas as pd

logger = logging.getLogger(__name__)


class TickAggregator:
    def __init__(self, flush_interval: int = 60):
        self.flush_interval = flush_interval
        self.candles_1s: Dict[str, Dict[str, Any]] = defaultdict(dict)
        self.candles_1m: Dict[str, Dict[str, Any]] = defaultdict(dict)
        self.lock = asyncio.Lock()

    async def aggregate_tick(self, tick: Dict[str, Any]):
        """Aggregates a tick into 1s and 1m candles."""
        symbol = tick["symbol"]
        ts_utc = tick["ts_utc"]

        async with self.lock:
            # Aggregate into 1s candle
            self._aggregate_candle(self.candles_1s, symbol, ts_utc, tick, 1)

            # Aggregate into 1m candle
            self._aggregate_candle(self.candles_1m, symbol, ts_utc, tick, 60)

    def _aggregate_candle(
        self,
        candles: Dict[str, Dict[str, Any]],
        symbol: str,
        ts_utc: str,
        tick: Dict[str, Any],
        interval: int,
    ):
        """Aggregates a tick into a candle."""
        # Determine the bucket key based on the timestamp and interval
        bucket_key = self._get_bucket_key(ts_utc, interval)

        if bucket_key not in candles[symbol]:
            # Create a new candle
            candles[symbol][bucket_key] = {
                "symbol": symbol,
                "ts_utc": bucket_key,
                "open": tick["price"],
                "high": tick["price"],
                "low": tick["price"],
                "close": tick["price"],
                "volume": tick["qty"] if "qty" in tick else 0,
            }
        else:
            # Update the existing candle
            candles[symbol][bucket_key]["high"] = max(
                candles[symbol][bucket_key]["high"], tick["price"]
            )
            candles[symbol][bucket_key]["low"] = min(
                candles[symbol][bucket_key]["low"], tick["price"]
            )
            candles[symbol][bucket_key]["close"] = tick["price"]
            candles[symbol][bucket_key]["volume"] += tick["qty"] if "qty" in tick else 0

    def _get_bucket_key(self, ts_utc: str, interval: int) -> str:
        """Determines the bucket key based on the timestamp and interval."""
        # Convert timestamp to datetime object
        ts = pd.to_datetime(ts_utc, utc=True)

        # Calculate the bucket start time
        bucket_start = ts - pd.Timedelta(seconds=ts.second % interval)

        # Convert bucket start time to string
        return str(bucket_start)

    async def flush_candles(self):
        """Flushes completed candles to the storage layer."""
        async with self.lock:
            # Flush 1s candles
            await self._flush_interval_candles(self.candles_1s, "1s")

            # Flush 1m candles
            await self._flush_interval_candles(self.candles_1m, "1m")

    async def _flush_interval_candles(self, candles: Dict[str, Dict[str, Any]], interval: str):
        """Flushes candles for a specific interval to the storage layer."""
        for symbol, interval_candles in candles.items():
            for bucket_key, candle in interval_candles.items():
                # Send candle to storage layer
                from market_data_ingestion.core.storage import DataStorage
                import yaml
                import os

                # Load config and initialize storage
                config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'config.example.yaml')
                with open(config_path, 'r') as f:
                    config = yaml.safe_load(f)

                storage = DataStorage(config['database']['db_path'])
                await storage.connect()
                await storage.insert_candle(candle)
                await storage.disconnect()

                logger.info(f"Flushed {interval} candle for {symbol} at {bucket_key}: {candle}")

            # Clear the candles for the interval
            candles[symbol].clear()

    async def run(self):
        """Runs the aggregator."""
        while True:
            await asyncio.sleep(self.flush_interval)
            await self.flush_candles()

async def main():
    # Example usage:
    logging.basicConfig(level=logging.DEBUG)
    aggregator = TickAggregator()
    # Simulate receiving ticks
    ticks = [
        {"symbol": "RELIANCE.NS", "ts_utc": "2024-01-01T10:00:00Z", "price": 2500.0, "qty": 10},
        {"symbol": "RELIANCE.NS", "ts_utc": "2024-01-01T10:00:01Z", "price": 2501.0, "qty": 5},
        {"symbol": "RELIANCE.NS", "ts_utc": "2024-01-01T10:00:59Z", "price": 2502.0, "qty": 12},
        {"symbol": "RELIANCE.NS", "ts_utc": "2024-01-01T10:01:00Z", "price": 2503.0, "qty": 8},
    ]

    for tick in ticks:
        await aggregator.aggregate_tick(tick)

    await aggregator.flush_candles()

if __name__ == "__main__":
    asyncio.run(main())
