"""Simple cache helper to reduce repeated DB work."""

from __future__ import annotations

import asyncio
import functools
import json
import logging
from typing import Any, Awaitable, Callable, ParamSpec, TypeVar

from cachetools import TTLCache

try:
    from redis.asyncio import Redis
except ImportError:  # pragma: no cover - optional dependency
    Redis = None  # type: ignore

from .config import settings

logger = logging.getLogger(__name__)
P = ParamSpec("P")
T = TypeVar("T")

_local_cache: TTLCache = TTLCache(maxsize=1024, ttl=settings.cache_ttl_seconds)
_redis_client: Redis | None = None


async def _get_redis_client() -> Redis | None:
    """Return a shared Redis client if configured."""
    global _redis_client
    if settings.redis_url is None or Redis is None:
        return None
    if _redis_client is None:
        _redis_client = Redis.from_url(settings.redis_url, encoding="utf-8", decode_responses=True)
    return _redis_client


def cached(key_builder: Callable[P, str]) -> Callable[[Callable[P, Awaitable[T]]], Callable[P, Awaitable[T]]]:
    """Decorator that caches async call results both locally and in Redis."""

    def decorator(func: Callable[P, Awaitable[T]]) -> Callable[P, Awaitable[T]]:
        @functools.wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            cache_key = key_builder(*args, **kwargs)

            # Local cache lookup
            if cache_key in _local_cache:
                return _local_cache[cache_key]

            redis_client = await _get_redis_client()
            if redis_client:
                cached_value = await redis_client.get(cache_key)
                if cached_value:
                    result = json.loads(cached_value)
                    _local_cache[cache_key] = result  # warm local cache
                    return result

            result = await func(*args, **kwargs)

            _local_cache[cache_key] = result
            if redis_client:
                try:
                    await redis_client.set(cache_key, json.dumps(result), ex=settings.cache_ttl_seconds)
                except Exception:  # pragma: no cover - logging only
                    logger.warning("Unable to persist cache entry for %s", cache_key, exc_info=True)
            return result

        return wrapper

    return decorator


async def invalidate(prefix: str) -> None:
    """Invalidate cached entries with a prefix."""
    keys_to_delete = [key for key in _local_cache.keys() if key.startswith(prefix)]
    for key in keys_to_delete:
        _local_cache.pop(key, None)

    redis_client = await _get_redis_client()
    if redis_client:
        async for key in redis_client.scan_iter(f"{prefix}*"):
            await redis_client.delete(key)
