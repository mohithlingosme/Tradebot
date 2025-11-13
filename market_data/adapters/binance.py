"""
Binance provider adapter.
"""

import asyncio
import hashlib
import hmac
import json
import logging
import time
from datetime import datetime, timedelta
from typing import AsyncGenerator, Dict, List
from urllib.parse import urlencode

import aiohttp
import websockets

from .base import ProviderAdapter

logger = logging.getLogger(__name__)


class BinanceAdapter(ProviderAdapter):
    """Adapter for Binance market data."""

    def __init__(self, config: Dict):
        super().__init__(config)
        self.base_url = config['base_url']
        self.api_key = config.get('api_key')
        self.api_secret = config.get('api_secret')
        self.session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    def get_provider_name(self) -> str:
        return "binance"

    def _generate_signature(self, params: Dict) -> str:
        """Generate HMAC SHA256 signature for authenticated requests."""
        query_string = urlencode(params)
        return hmac.new(
            self.api_secret.encode('utf-8'),
            query_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()

    async def stream_trades(self, symbol: str) -> AsyncGenerator[Dict, None]:
        """Stream real-time trades from Binance WebSocket."""
        ws_url = f"wss://stream.binance.com:9443/ws/{symbol.lower()}@trade"

        try:
            async with websockets.connect(ws_url) as websocket:
                async for message in websocket:
                    data = json.loads(message)

                    if data.get("stream") == f"{symbol.lower()}@trade":
                        trade_data = data.get("data", {})
                        yield {
                            "trade_id": str(trade_data.get("t")),
                            "price": float(trade_data.get("p", 0)),
                            "size": float(trade_data.get("q", 0)),
                            "event_time": datetime.fromtimestamp(trade_data.get("T", 0) / 1000),
                            "side": "buy" if trade_data.get("m") else "sell",  # m=True means buyer is market maker
                            "symbol": symbol
                        }
        except Exception as e:
            logger.error(f"Binance WebSocket error: {e}")
            raise

    async def fetch_trades(self, symbol: str, start_time: datetime,
                          end_time: datetime) -> List[Dict]:
        """Fetch historical trades from Binance REST API."""
        if not self.session:
            raise RuntimeError("Adapter not initialized with session")

        trades = []
        current_time = start_time

        while current_time < end_time:
            chunk_end = min(current_time + timedelta(hours=1), end_time)

            params = {
                "symbol": symbol.upper(),
                "startTime": int(current_time.timestamp() * 1000),
                "endTime": int(chunk_end.timestamp() * 1000),
                "limit": 1000
            }

            url = f"{self.base_url}/api/v3/aggTrades?{urlencode(params)}"

            try:
                async with self.session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        for trade in data:
                            trades.append({
                                "trade_id": str(trade.get("a")),
                                "price": float(trade.get("p", 0)),
                                "size": float(trade.get("q", 0)),
                                "event_time": datetime.fromtimestamp(trade.get("T", 0) / 1000),
                                "side": "unknown",  # Aggregate trades don't have side
                                "symbol": symbol
                            })
                    else:
                        logger.warning(f"Binance API error: {response.status}")

            except Exception as e:
                logger.error(f"Error fetching trades from Binance: {e}")

            current_time = chunk_end
            await asyncio.sleep(0.1)  # Rate limiting

        return trades

    async def stream_quotes(self, symbol: str) -> AsyncGenerator[Dict, None]:
        """Stream real-time quotes from Binance WebSocket."""
        ws_url = f"wss://stream.binance.com:9443/ws/{symbol.lower()}@bookTicker"

        try:
            async with websockets.connect(ws_url) as websocket:
                async for message in websocket:
                    data = json.loads(message)

                    if data.get("stream") == f"{symbol.lower()}@bookTicker":
                        quote_data = data.get("data", {})
                        yield {
                            "bid_price": float(quote_data.get("b", 0)),
                            "bid_size": float(quote_data.get("B", 0)),
                            "ask_price": float(quote_data.get("a", 0)),
                            "ask_size": float(quote_data.get("A", 0)),
                            "event_time": datetime.fromtimestamp(quote_data.get("T", 0) / 1000),
                            "symbol": symbol
                        }
        except Exception as e:
            logger.error(f"Binance WebSocket error: {e}")
            raise

    async def fetch_candles(self, symbol: str, interval: str,
                           start_time: datetime, end_time: datetime) -> List[Dict]:
        """Fetch historical candles from Binance REST API."""
        if not self.session:
            raise RuntimeError("Adapter not initialized with session")

        # Convert interval to Binance format
        interval_map = {
            '1m': '1m',
            '5m': '5m',
            '15m': '15m',
            '1h': '1h',
            '1d': '1d'
        }

        binance_interval = interval_map.get(interval, '1m')

        params = {
            "symbol": symbol.upper(),
            "interval": binance_interval,
            "startTime": int(start_time.timestamp() * 1000),
            "endTime": int(end_time.timestamp() * 1000),
            "limit": 1000
        }

        url = f"{self.base_url}/api/v3/klines?{urlencode(params)}"

        try:
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    return [{
                        "open": float(candle[1]),
                        "high": float(candle[2]),
                        "low": float(candle[3]),
                        "close": float(candle[4]),
                        "volume": float(candle[5]),
                        "event_time": datetime.fromtimestamp(candle[0] / 1000),
                        "symbol": symbol,
                        "interval": interval
                    } for candle in data]
                else:
                    logger.warning(f"Binance API error: {response.status}")
                    return []
        except Exception as e:
            logger.error(f"Error fetching candles from Binance: {e}")
            return []
