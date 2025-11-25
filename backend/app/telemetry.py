"""Telemetry utilities for metrics and tracing."""

import logging
from typing import Any

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from .config import settings

try:
    import sentry_sdk  # type: ignore
    from sentry_sdk.integrations.fastapi import FastApiIntegration
except ImportError:  # pragma: no cover - optional dependency
    sentry_sdk = None  # type: ignore

    class FastApiIntegration:
        """Placeholder when sentry-sdk is not installed."""

        pass

logger = logging.getLogger(__name__)


class RequestTimingMiddleware(BaseHTTPMiddleware):
    """Adds simple timing headers for observability."""

    async def dispatch(self, request: Request, call_next: Any) -> Response:
        start = request.scope.get("_start_time")
        if start is None:
            import time

            start = time.perf_counter()
            request.scope["_start_time"] = start
        response = await call_next(request)
        import time

        duration_ms = (time.perf_counter() - start) * 1000
        response.headers["X-Response-Time-ms"] = f"{duration_ms:.2f}"
        return response


def configure_sentry() -> None:
    """Configure Sentry if DSN is provided and available."""
    if settings.sentry_dsn and sentry_sdk is not None:
        sentry_sdk.init(
            dsn=settings.sentry_dsn,
            integrations=[FastApiIntegration()],
            traces_sample_rate=0.2,
        )
        logger.info("Sentry initialized")
