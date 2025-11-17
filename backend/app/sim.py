"""
Market data simulator for generating realistic mock data.
"""
import random
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import asyncio

class MarketDataSimulator:
    """Simulates realistic market data for testing and development."""

    def __init__(self):
        self.symbols = [
            "AAPL", "GOOGL", "MSFT", "TSLA", "AMZN",
            "NVDA", "META", "NFLX", "BABA", "ORCL"
        ]
        self.base_prices = {}
        self.volatility = {}
        self.trends = {}

        # Initialize base data
        for symbol in self.symbols:
            self.base_prices[symbol] = 100 + random.random() * 200
            self.volatility[symbol] = 0.01 + random.random() * 0.05  # 1-6% volatility
            self.trends[symbol] = (random.random() - 0.5) * 0.001  # Slight trend

    def generate_candle(
        self,
        symbol: str,
        timestamp: datetime,
        interval_minutes: int = 1
    ) -> Dict:
        """Generate a single candle for the given symbol and timestamp."""
        if symbol not in self.base_prices:
            raise ValueError(f"Unknown symbol: {symbol}")

        base_price = self.base_prices[symbol]
        volatility = self.volatility[symbol]
        trend = self.trends[symbol]

        # Add trend component
        trend_factor = trend * (timestamp.timestamp() / 86400)  # Days since epoch
        current_price = base_price * (1 + trend_factor)

        # Add random walk
        price_change = random.gauss(0, volatility * current_price)
        open_price = current_price + price_change

        # Generate OHLC
        high_offset = abs(random.gauss(0, volatility * current_price * 0.5))
        low_offset = abs(random.gauss(0, volatility * current_price * 0.5))
        close_offset = random.gauss(0, volatility * current_price * 0.3)

        high_price = open_price + high_offset
        low_price = open_price - low_offset
        close_price = open_price + close_offset

        # Ensure OHLC relationships
        high_price = max(high_price, open_price, close_price)
        low_price = min(low_price, open_price, close_price)

        # Generate volume (simplified)
        base_volume = 100000 + random.random() * 900000
        volume_multiplier = 1 + abs(close_offset / open_price) * 2  # Higher volume on bigger moves
        volume = int(base_volume * volume_multiplier)

        return {
            "symbol": symbol,
            "timestamp": int(timestamp.timestamp() * 1000),  # milliseconds
            "open": round(open_price, 2),
            "high": round(high_price, 2),
            "low": round(low_price, 2),
            "close": round(close_price, 2),
            "volume": volume
        }

    def generate_candles(
        self,
        symbol: str,
        start_time: datetime,
        end_time: datetime,
        interval_minutes: int = 1
    ) -> List[Dict]:
        """Generate a series of candles."""
        candles = []
        current_time = start_time

        while current_time <= end_time:
            candle = self.generate_candle(symbol, current_time, interval_minutes)
            candles.append(candle)
            current_time += timedelta(minutes=interval_minutes)

        return candles

    def generate_realtime_update(self, symbol: str) -> Dict:
        """Generate a real-time price update."""
        if symbol not in self.base_prices:
            raise ValueError(f"Unknown symbol: {symbol}")

        current_price = self.base_prices[symbol]
        volatility = self.volatility[symbol]

        # Generate price movement
        price_change = random.gauss(0, volatility * current_price * 0.1)
        new_price = current_price + price_change

        # Update stored price
        self.base_prices[symbol] = new_price

        return {
            "type": "price_update",
            "symbol": symbol,
            "price": round(new_price, 2),
            "change": round(price_change, 2),
            "change_percent": round((price_change / (new_price - price_change)) * 100, 2),
            "timestamp": datetime.utcnow().isoformat(),
            "volume": int(random.random() * 10000)
        }

    async def stream_realtime_updates(
        self,
        symbols: List[str],
        interval_seconds: float = 1.0
    ):
        """Async generator for real-time price updates."""
        while True:
            for symbol in symbols:
                if random.random() < 0.3:  # 30% chance of update per symbol per interval
                    yield self.generate_realtime_update(symbol)

            await asyncio.sleep(interval_seconds)

# Global simulator instance
simulator = MarketDataSimulator()

if __name__ == "__main__":
    # Example usage
    sim = MarketDataSimulator()

    # Generate some sample candles
    start = datetime.now() - timedelta(hours=1)
    end = datetime.now()

    candles = sim.generate_candles("AAPL", start, end, interval_minutes=5)
    print(f"Generated {len(candles)} candles for AAPL")

    for candle in candles[:3]:
        print(candle)

    # Generate real-time update
    update = sim.generate_realtime_update("AAPL")
    print(f"Real-time update: {update}")
