import asyncio
import json
import logging
import random
import time
from datetime import datetime, timezone
from typing import Any, Awaitable, Callable, Dict, List, Optional

import tenacity
import websockets

from market_data_ingestion.adapters.base import BaseMarketDataAdapter, NormalizedTick
from market_data_ingestion.src.logging_config import get_logger

logger = get_logger(__name__)


class KiteWebSocketAdapter(BaseMarketDataAdapter):
    provider = "kite"

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.api_key = config.get("api_key")
        self.api_secret = config.get("api_secret")
        self.websocket_url = config.get("websocket_url", "ws://localhost:8765")  # Mock server URL
        self.reconnect_interval = config.get("reconnect_interval", 5)
        self.symbols: List[str] = []
        self.ws: Optional[websockets.WebSocketClientProtocol] = None
        self._tick_handler: Optional[Callable[[NormalizedTick], Awaitable[None]]] = None

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    def set_tick_handler(self, handler: Callable[[NormalizedTick], Awaitable[None]]):
        """Register a coroutine that will receive each normalized tick."""
        self._tick_handler = handler

    async def authenticate(self):
        logger.info("Authenticating with Kite API (mock)")
        await asyncio.sleep(1)  # Simulate authentication delay
        return True

    async def subscribe(self, symbols: List[str]):
        logger.info(f"Subscribing to symbols: {symbols} (mock)")
        self.symbols = symbols
        await asyncio.sleep(1)  # Simulate subscription delay

    async def close(self) -> None:
        if self.ws:
            await self.ws.close()
        await self._mark_connected(False)

    async def _send_heartbeat(self):
        while True:
            try:
                await self.ws.ping()
                logger.debug("Sent heartbeat to server")
                await asyncio.sleep(self.config.get("heartbeat_interval", 30))  # Send heartbeat every 30 seconds
            except Exception as e:
                logger.error(f"Error sending heartbeat: {e}")
                break

    @tenacity.retry(
        stop=tenacity.stop_after_attempt(5),
        wait=tenacity.wait_exponential(multiplier=1, min=4, max=30),
        retry=tenacity.retry_if_exception_type(Exception),
        before_sleep=tenacity.before_sleep_log(logger, logging.WARNING)
    )
    async def connect(self):
        """Connects to the Kite WebSocket."""
        try:
            async with websockets.connect(self.websocket_url) as ws:
                self.ws = ws
                logger.info(f"Connected to Kite WebSocket: {self.websocket_url}")
                await self._mark_connected(True)

                # Authenticate with the Kite API
                if not await self.authenticate():
                    logger.error("Authentication failed. Disconnecting.")
                    return

                # Subscribe to the list of symbols
                await self.subscribe(self.symbols)

                # Start heartbeat task
                heartbeat_task = asyncio.create_task(self._send_heartbeat())

                # Start receiving messages
                async for tick in self.stream():
                    if self._tick_handler:
                        await self._tick_handler(tick)
                    else:
                        logger.debug(f"Tick: {tick.to_dict()}")

                # Cancel heartbeat task if the connection closes
                heartbeat_task.cancel()

        except Exception as e:
            logger.error(f"Connection error: {e}")
            raise
        finally:
            await self._mark_connected(False)

    async def stream(self):
        """Receives messages from the WebSocket and processes them."""
        try:
            async for message in self.ws:
                tick = await self.process_message(message)
                if tick:
                    yield tick
        except websockets.exceptions.ConnectionClosedError as e:
            logger.error(f"Connection closed: {e}")
        except Exception as e:
            logger.error(f"Error receiving messages: {e}")
        finally:
            logger.info("Disconnected from Kite WebSocket")

    async def process_message(self, message: str):
        """Processes a message received from the WebSocket."""
        try:
            data = json.loads(message)
            normalized_data = self._normalize_data(data)
            return normalized_data
        except json.JSONDecodeError:
            logger.warning(f"Received non-JSON message: {message}")
        except Exception as e:
            logger.error(f"Error processing message: {e}")
        return None

    def _normalize_data(self, data: Dict[str, Any]) -> NormalizedTick:
        """Normalizes the data to a unified JSON structure based on Kite websocket format."""
        timestamp = data.get("timestamp")
        if isinstance(timestamp, str):
            ts = datetime.fromisoformat(timestamp.replace("Z", "+00:00")).astimezone(timezone.utc)
        else:
            ts = datetime.fromtimestamp(timestamp or time.time(), tz=timezone.utc)

        return NormalizedTick(
            symbol=str(data.get("instrument_token", "UNKNOWN")),
            ts_utc=ts,
            price=self._normalize_price(data.get("last_price", 0.0)),
            volume=float(data.get("volume", 0) or data.get("last_quantity", 0) or 0),
            provider=self.provider,
            raw=data,
        )

    async def realtime_connect(self, symbols: List[str]):
        """Connects to the WebSocket and subscribes to the given symbols."""
        self.symbols = symbols
        while True:
            try:
                await self.connect()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Failed to connect. Retrying in {self.reconnect_interval} seconds...: {e}")
            await asyncio.sleep(self.reconnect_interval)

async def main():
    # Example usage:
    logging.basicConfig(level=logging.DEBUG)
    config = {
        "api_key": "YOUR_API_KEY",
        "api_secret": "YOUR_API_SECRET",
        "websocket_url": "ws://localhost:8765",  # Replace with your mock server URL
    }
    symbols = ["RELIANCE.NS", "TCS.NS"]

    async with KiteWebSocketAdapter(config) as adapter:
        await adapter.realtime_connect(symbols)
        # Keep the connection alive for some time
        await asyncio.sleep(60)

if __name__ == "__main__":
    asyncio.run(main())
