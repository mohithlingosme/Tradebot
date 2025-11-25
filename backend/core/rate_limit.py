"""
Rate limiting middleware for FastAPI
"""

import time
from typing import Optional
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
import logging

logger = logging.getLogger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware using in-memory storage."""

    def __init__(self, app, requests_per_minute: int = 60, requests_per_hour: int = 1000):
        """
        Initialize rate limiter.

        Args:
            app: FastAPI application
            requests_per_minute: Maximum requests per minute per IP
            requests_per_hour: Maximum requests per hour per IP
        """
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.requests_per_hour = requests_per_hour
        self.request_times: dict[str, list[float]] = {}

    def get_client_ip(self, request: Request) -> str:
        """Get client IP address."""
        if "x-forwarded-for" in request.headers:
            return request.headers["x-forwarded-for"].split(",")[0].strip()
        return request.client.host if request.client else "unknown"

    def is_rate_limited(self, ip: str) -> tuple[bool, Optional[str]]:
        """
        Check if IP is rate limited.

        Returns:
            Tuple of (is_limited, error_message)
        """
        now = time.time()
        
        # Initialize if not exists
        if ip not in self.request_times:
            self.request_times[ip] = []

        # Clean old entries (older than 1 hour)
        self.request_times[ip] = [
            t for t in self.request_times[ip] if now - t < 3600
        ]

        # Check per-minute limit
        recent_minute = [t for t in self.request_times[ip] if now - t < 60]
        if len(recent_minute) >= self.requests_per_minute:
            return True, f"Rate limit exceeded: {self.requests_per_minute} requests per minute"

        # Check per-hour limit
        if len(self.request_times[ip]) >= self.requests_per_hour:
            return True, f"Rate limit exceeded: {self.requests_per_hour} requests per hour"

        # Add current request
        self.request_times[ip].append(now)
        return False, None

    async def dispatch(self, request: Request, call_next):
        """Process request with rate limiting."""
        # Skip rate limiting for health checks
        if request.url.path in ["/health", "/ready", "/metrics"]:
            return await call_next(request)

        ip = self.get_client_ip(request)
        is_limited, error_msg = self.is_rate_limited(ip)

        if is_limited:
            logger.warning(f"Rate limit exceeded for IP: {ip}")
            return Response(
                content=error_msg or "Rate limit exceeded",
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                headers={"Retry-After": "60"}
            )

        response = await call_next(request)
        return response

