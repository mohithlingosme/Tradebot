"""Telemetry utilities for metrics and tracing."""

import logging
from typing import Any

import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from .config import settings

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
    """Configure Sentry if DSN is provided."""
    if settings.sentry_dsn:
        sentry_sdk.init(dsn=settings.sentry_dsn, integrations=[FastApiIntegration()], traces_sample_rate=0.2)
        logger.info("Sentry initialized")
