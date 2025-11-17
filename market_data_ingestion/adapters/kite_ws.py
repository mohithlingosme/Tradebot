import asyncio
import json
import logging
import random
import time
from typing import Dict, Any, List

import websockets

logger = logging.getLogger(__name__)


class KiteWebSocketAdapter:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.api_key = config.get("api_key")
        self.api_secret = config.get("api_secret")
        self.websocket_url = config.get("websocket_url", "ws://localhost:8765")  # Mock server URL
        self.reconnect_interval = config.get("reconnect_interval", 5)
        self.symbols = []
        self.ws = None

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.ws:
            await self.ws.close()

    async def authenticate(self):
        # In a real implementation, this would involve authenticating with the Kite API
        # using the API key and secret. For the mock server, we just log a message.
        logger.info("Authenticating with Kite API (mock)")
        await asyncio.sleep(1)  # Simulate authentication delay
        return True

    async def subscribe(self, symbols: List[str]):
        # In a real implementation, this would involve subscribing to the provided symbols
        # via the Kite websocket. For the mock server, we just log a message.
        logger.info(f"Subscribing to symbols: {symbols} (mock)")
        self.symbols = symbols
        await asyncio.sleep(1)  # Simulate subscription delay

    async def _send_heartbeat(self):
        while True:
            try:
                # Send a ping message to the server
                await self.ws.ping()
                logger.debug("Sent heartbeat to server")
                await asyncio.sleep(self.config.get("heartbeat_interval", 30))  # Send heartbeat every 30 seconds
            except Exception as e:
                logger.error(f"Error sending heartbeat: {e}")
                break

    async def connect(self):
        """Connects to the Kite WebSocket."""
        try:
            async with websockets.connect(self.websocket_url) as ws:
                self.ws = ws
                logger.info(f"Connected to Kite WebSocket: {self.websocket_url}")

                # Authenticate with the Kite API
                if not await self.authenticate():
                    logger.error("Authentication failed. Disconnecting.")
                    return

                # Subscribe to the list of symbols
                await self.subscribe(self.symbols)

                # Start heartbeat task
                heartbeat_task = asyncio.create_task(self._send_heartbeat())

                # Start receiving messages
                await self.receive_messages()

                # Cancel heartbeat task if the connection closes
                heartbeat_task.cancel()

        except Exception as e:
            logger.error(f"Connection error: {e}")
            raise

    async def receive_messages(self):
        """Receives messages from the WebSocket and processes them."""
        try:
            async for message in self.ws:
                #logger.debug(f"Received message: {message}")
                await self.process_message(message)
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
            #logger.debug(f"Parsed message data: {data}")

            # Normalize the data
            normalized_data = self._normalize_data(data, "kite")

            # Send to aggregator
            from market_data_ingestion.core.aggregator import TickAggregator
            aggregator = TickAggregator()
            await aggregator.aggregate_tick(normalized_data)
            await aggregator.flush_candles()  # Flush immediately for demo

            # Process the normalized data (e.g., send to a channel for aggregation)
            # For now, just print the normalized data
            print(f"Normalized data: {normalized_data}")
        except json.JSONDecodeError:
            logger.warning(f"Received non-JSON message: {message}")
        except Exception as e:
            logger.error(f"Error processing message: {e}")

    def _normalize_data(self, data: Dict[str, Any], provider: str) -> Dict[str, Any]:
        """Normalizes the data to a unified JSON structure."""
        # This is a placeholder implementation.  You will need to adjust this
        # based on the actual data format received from the Kite websocket.
        return {
            "symbol": data.get("instrument", "UNKNOWN"),
            "ts_utc": time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(data.get("timestamp", time.time()))),
            "type": "trade",
            "price": data.get("last_price", 0.0),
            "qty": data.get("last_quantity", 0),
            "open": data.get("open", 0.0),
            "high": data.get("high", 0.0),
            "low": data.get("low", 0.0),
            "close": data.get("close", 0.0),
            "volume": data.get("volume", 0),
            "provider": provider,
            "meta": {},
        }

    async def realtime_connect(self, symbols: List[str]):
        """Connects to the WebSocket and subscribes to the given symbols."""
        self.symbols = symbols
        while True:
            try:
                await self.connect()
                break  # If connection was successful, exit the loop
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
