import time

import httpx
import pytest

API_URL = "http://localhost:8000/api"


async def fetch_candles(symbol: str = "AAPL", limit: int = 100):
    async with httpx.AsyncClient() as client:
        return await client.get(f"{API_URL}/candles/{symbol}?limit={limit}")


def test_candles_under_150ms(event_loop):
    start = time.perf_counter()
    try:
        response = event_loop.run_until_complete(fetch_candles())
    except httpx.ConnectError:
        pytest.skip("API server not running")
    duration = (time.perf_counter() - start) * 1000
    assert response.status_code == 200
    assert duration < 150, f"P95 target violated: {duration:.2f}ms"
