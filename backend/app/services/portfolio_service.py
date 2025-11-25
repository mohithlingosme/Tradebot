"""Business logic for portfolio operations."""

from ..config import settings
from ..managers import PortfolioManager

cache = None  # placeholder assigned below


class PortfolioService:
    def __init__(self, manager: PortfolioManager) -> None:
        self._manager = manager

    async def get_portfolio(self, user_id: str):
        global cache
        if cache is None:
            from .cache import SimpleCache

            cache = SimpleCache()

        cache_key = f"portfolio:{user_id}"
        cached_snapshot = cache.get(cache_key)
        if cached_snapshot:
            return cached_snapshot

        snapshot = await self._manager.snapshot(user_id)
        cache.set(cache_key, snapshot, settings.cache_ttl_seconds)
        return snapshot


portfolio_service = PortfolioService(PortfolioManager())
