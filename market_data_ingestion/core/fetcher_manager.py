import asyncio
import logging
from typing import List, Dict, Any, Callable

logger = logging.getLogger(__name__)


class FetcherManager:
    def __init__(self, max_concurrent_tasks: int = 5):
        self.max_concurrent_tasks = max_concurrent_tasks
        self.semaphore = asyncio.Semaphore(max_concurrent_tasks)

    async def fetch_data(
        self,
        symbols: List[str],
        data_fetcher: Callable[[str], List[Dict[str, Any]]],
    ) -> List[Dict[str, Any]]:
        """Fetches data for a list of symbols using the provided data fetcher."""
        async with self.semaphore:
            try:
                data = await data_fetcher(symbols)
                return data
            except Exception as e:
                logger.error(f"Error fetching data for symbols {symbols}: {e}")
                return []

    async def run_backfill(
        self,
        symbols: List[str],
        data_fetcher: Callable[[List[str]], List[Dict[str, Any]]],
    ):
        """Runs a backfill for the given symbols using the provided data fetcher."""
        tasks = []
        for symbol in symbols:
            task = asyncio.create_task(self.fetch_data([symbol], data_fetcher))
            tasks.append(task)

        # Gather the results as they complete
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process the results
        for symbol, result in zip(symbols, results):
            if isinstance(result, Exception):
                logger.error(f"Backfill failed for {symbol}: {result}")
            else:
                logger.info(f"Backfill completed for {symbol}: {len(result)} records fetched")

async def main():
    # Example usage:
    logging.basicConfig(level=logging.DEBUG)
    manager = FetcherManager()

    async def mock_data_fetcher(symbols: List[str]) -> List[Dict[str, Any]]:
        """Mocks a data fetcher that returns sample data."""
        await asyncio.sleep(1)  # Simulate network delay
        data = []
        for symbol in symbols:
            data.append(
                {
                    "symbol": symbol,
                    "ts_utc": "2024-01-01T00:00:00Z",
                    "open": 100.0,
                    "high": 101.0,
                    "low": 99.0,
                    "close": 100.5,
                    "volume": 1000,
                }
            )
        return data

    symbols = ["RELIANCE.NS", "TCS.NS", "INFY.NS"]
    await manager.run_backfill(symbols, mock_data_fetcher)

if __name__ == "__main__":
    asyncio.run(main())
