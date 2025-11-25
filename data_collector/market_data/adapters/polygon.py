"""
Polygon.io provider adapter.
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import AsyncGenerator, Dict, List
from urllib.parse import urlencode

import aiohttp
import websockets

from .base import ProviderAdapter

logger = logging.getLogger(__name__)


class PolygonAdapter(ProviderAdapter):
    """Adapter for Polygon.io market data."""

    def __init__(self, config: Dict):
        super().__init__(config)
        self.base_url = config['base_url']
        self.api_key = config['api_key']
        self.session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    def get_provider_name(self) -> str:
        return "polygon"

    async def stream_trades(self, symbol: str) -> AsyncGenerator[Dict, None]:
        """Stream real-time trades from Polygon WebSocket."""
        ws_url = f"wss://socket.polygon.io/stocks"
        subscribe_msg = {
            "action": "subscribe",
            "params": f"T.{symbol}"
        }

        try:
            async with websockets.connect(ws_url) as websocket:
                await websocket.send(json.dumps(subscribe_msg))

                async for message in websocket:
                    data = json.loads(message)

                    if data.get("ev") == "T":  # Trade event
                        yield {
                            "trade_id": str(data.get("i")),
                            "price": float(data.get("p", 0)),
                            "size": float(data.get("s", 0)),
                            "event_time": datetime.fromtimestamp(data.get("t", 0) / 1000),
                            "side": "unknown",  # Polygon doesn't provide side
                            "symbol": symbol
                        }
        except Exception as e:
            logger.error(f"Polygon WebSocket error: {e}")
            raise

    async def fetch_trades(self, symbol: str, start_time: datetime,
                          end_time: datetime) -> List[Dict]:
        """Fetch historical trades from Polygon REST API."""
        if not self.session:
            raise RuntimeError("Adapter not initialized with session")

        trades = []
        current_time = start_time

        while current_time < end_time:
            chunk_end = min(current_time + timedelta(days=1), end_time)

            params = {
                "apiKey": self.api_key,
                "timestamp": int(current_time.timestamp() * 1000),
                "timestampLimit": int(chunk_end.timestamp() * 1000),
                "limit": 50000
            }

            url = f"{self.base_url}/v3/trades/{symbol}?{urlencode(params)}"

            try:
                async with self.session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        for trade in data.get("results", []):
                            trades.append({
                                "trade_id": str(trade.get("id")),
                                "price": float(trade.get("price", 0)),
                                "size": float(trade.get("size", 0)),
                                "event_time": datetime.fromtimestamp(trade.get("timestamp", 0) / 1000000000),
                                "side": "unknown",
                                "symbol": symbol
                            })
                    else:
                        logger.warning(f"Polygon API error: {response.status}")

            except Exception as e:
                logger.error(f"Error fetching trades from Polygon: {e}")

            current_time = chunk_end
            await asyncio.sleep(0.1)  # Rate limiting

        return trades

    async def stream_quotes(self, symbol: str) -> AsyncGenerator[Dict, None]:
        """Stream real-time quotes from Polygon WebSocket."""
        ws_url = f"wss://socket.polygon.io/stocks"
        subscribe_msg = {
            "action": "subscribe",
            "params": f"Q.{symbol}"
        }

        try:
            async with websockets.connect(ws_url) as websocket:
                await websocket.send(json.dumps(subscribe_msg))

                async for message in websocket:
                    data = json.loads(message)

                    if data.get("ev") == "Q":  # Quote event
                        yield {
                            "bid_price": float(data.get("bp", 0)),
                            "bid_size": float(data.get("bs", 0)),
                            "ask_price": float(data.get("ap", 0)),
                            "ask_size": float(data.get("as", 0)),
                            "event_time": datetime.fromtimestamp(data.get("t", 0) / 1000),
                            "symbol": symbol
                        }
        except Exception as e:
            logger.error(f"Polygon WebSocket error: {e}")
            raise

    async def fetch_candles(self, symbol: str, interval: str,
                           start_time: datetime, end_time: datetime) -> List[Dict]:
        """Fetch historical candles from Polygon REST API."""
        if not self.session:
            raise RuntimeError("Adapter not initialized with session")

        # Convert interval to Polygon format
        interval_map = {
            '1m': 'minute',
            '5m': '5',
            '15m': '15',
            '1h': 'hour',
            '1d': 'day'
        }

        multiplier = 1
        timespan = interval_map.get(interval, 'minute')

        if interval.endswith('m'):
            multiplier = int(interval[:-1])
            timespan = 'minute'
        elif interval.endswith('h'):
            multiplier = int(interval[:-1])
            timespan = 'hour'
        elif interval.endswith('d'):
            multiplier = int(interval[:-1])
            timespan = 'day'

        params = {
            "apiKey": self.api_key,
            "timestamp.gte": int(start_time.timestamp() * 1000),
            "timestamp.lte": int(end_time.timestamp() * 1000),
            "multiplier": multiplier,
            "timespan": timespan,
            "limit": 50000
        }

        url = f"{self.base_url}/v2/aggs/ticker/{symbol}/range/{multiplier}/{timespan}/{start_time.strftime('%Y-%m-%d')}/{end_time.strftime('%Y-%m-%d')}?{urlencode(params)}"

        try:
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    return [{
                        "open": float(candle.get("o", 0)),
                        "high": float(candle.get("h", 0)),
                        "low": float(candle.get("l", 0)),
                        "close": float(candle.get("c", 0)),
                        "volume": float(candle.get("v", 0)),
                        "event_time": datetime.fromtimestamp(candle.get("t", 0) / 1000),
                        "symbol": symbol,
                        "interval": interval
                    } for candle in data.get("results", [])]
                else:
                    logger.warning(f"Polygon API error: {response.status}")
                    return []
        except Exception as e:
            logger.error(f"Error fetching candles from Polygon: {e}")
            return []
