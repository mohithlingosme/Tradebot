import asyncio
import json
import logging
import random
import time
from typing import Dict, Any, List

import websockets

logger = logging.getLogger(__name__)


class MockWebSocketServer:
    def __init__(self, host: str = "localhost", port: int = 8765):
        self.host = host
        self.port = port
        self.server = None

    async def start(self):
        """Starts the mock WebSocket server."""
        async def handler(websocket, path):
            logger.info("New connection established")

            try:
                # Simulate authentication
                await asyncio.sleep(1)
                await websocket.send(json.dumps({"type": "auth", "status": "success"}))

                # Simulate subscription
                await asyncio.sleep(1)
                await websocket.send(json.dumps({"type": "subscribe", "status": "success"}))

                # Start sending mock data
                await self.send_mock_data(websocket)

            except websockets.exceptions.ConnectionClosed:
                logger.info("Connection closed")
            except Exception as e:
                logger.error(f"Error handling connection: {e}")

        self.server = await websockets.serve(handler, self.host, self.port)
        logger.info(f"Mock WebSocket server started on ws://{self.host}:{self.port}")
        await self.server.wait_closed()

    async def send_mock_data(self, websocket):
        """Sends mock market data to the connected client."""
        symbols = ["RELIANCE.NS", "TCS.NS", "INFY.NS"]
        base_prices = {"RELIANCE.NS": 2500.0, "TCS.NS": 3200.0, "INFY.NS": 1400.0}

        while True:
            try:
                for symbol in symbols:
                    # Generate mock tick data
                    base_price = base_prices[symbol]
                    price_change = random.uniform(-0.01, 0.01)  # Random price change
                    new_price = base_price * (1 + price_change)
                    base_prices[symbol] = new_price

                    depth = {
                        "buy": [
                            {"price": round(new_price - 0.05 * level, 2), "size": random.randint(50, 500)}
                            for level in range(1, 6)
                        ],
                        "sell": [
                            {"price": round(new_price + 0.05 * level, 2), "size": random.randint(50, 500)}
                            for level in range(1, 6)
                        ],
                    }

                    tick_data = {
                        "instrument": symbol,
                        "timestamp": time.time(),
                        "last_price": round(new_price, 2),
                        "last_quantity": random.randint(1, 100),
                        "open": round(base_price * 0.99, 2),
                        "high": round(base_price * 1.01, 2),
                        "low": round(base_price * 0.98, 2),
                        "close": round(new_price, 2),
                        "volume": random.randint(1000, 10000),
                        "depth": depth,
                    }

                    await websocket.send(json.dumps(tick_data))
                    logger.debug(f"Sent mock data: {tick_data}")

                await asyncio.sleep(1)  # Send data every second

            except websockets.exceptions.ConnectionClosed:
                break
            except Exception as e:
                logger.error(f"Error sending mock data: {e}")
                break

    async def stop(self):
        """Stops the mock WebSocket server."""
        if self.server:
            self.server.close()
            await self.server.wait_closed()
            logger.info("Mock WebSocket server stopped")


async def main():
    # Start the mock server
    server = MockWebSocketServer()
    try:
        await server.start()
    except KeyboardInterrupt:
        await server.stop()


if __name__ == "__main__":
    asyncio.run(main())
