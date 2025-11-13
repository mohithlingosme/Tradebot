import yfinance as yf
import pandas as pd
from typing import Dict, Any, Optional

class YFinanceAdapter:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.rate_limit_delay = 60 / config.get("rate_limit_per_minute", 100)  # Delay in seconds

    async def fetch_historical_data(
        self, symbol: str, start: str, end: str, interval: str = "1m"
    ) -> list[Dict[str, Any]]:
        '''Fetches historical data from yfinance.

        Args:
            symbol (str): The symbol to fetch data for (e.g., "RELIANCE.NS").
            start (str): The start date in "YYYY-MM-DD" format.
            end (str): The end date in "YYYY-MM-DD" format.
            interval (str): The interval (e.g., "1m", "5m", "1d").

        Returns:
            list[Dict[str, Any]]: A list of normalized data dictionaries.
        '''
        try:
            # Download data from yfinance
            data = yf.download(symbol, start=start, end=end, interval=interval)

            # Normalize the data
            normalized_data = self._normalize_data(symbol, data, interval, "yfinance")
            return normalized_data
        except Exception as e:
            print(f"Error fetching data for {symbol}: {e}")
            return []

    def _normalize_data(self, symbol: str, data: pd.DataFrame, interval: str, provider: str) -> list[Dict[str, Any]]:
        '''Normalizes the data to a unified JSON structure.

        Args:
            symbol (str): The symbol of the data.
            data (pd.DataFrame): The data from yfinance.
            interval (str): The interval of the data.
            provider (str): The data provider name.

        Returns:
            list[Dict[str, Any]]: A list of normalized data dictionaries.
        '''
        normalized_data = []
        for index, row in data.iterrows():
            normalized_data.append(
                {
                    "symbol": symbol,
                    "ts_utc": str(index),
                    "type": "candle",
                    "open": row["Open"],
                    "high": row["High"],
                    "low": row["Low"],
                    "close": row["Close"],
                    "volume": row["Volume"],
                    "provider": provider,
                    "meta": {},
                }
            )
        return normalized_data

    async def realtime_connect(self, symbols: list[str]):
        # yfinance doesn't support realtime data
        raise NotImplementedError("yfinance does not support realtime data")
