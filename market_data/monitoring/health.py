"""
Health check endpoints for the market data ingestion system.
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any

from aiohttp import web
from ..storage.writer import DataWriter

logger = logging.getLogger(__name__)


class HealthChecker:
    """Health check service for market data ingestion."""

    def __init__(self, writer: DataWriter, port: int = 8000):
        self.writer = writer
        self.port = port
        self.app = web.Application()
        self.runner = None
        self.site = None
        self.last_health_check = datetime.utcnow()
        self.healthy = True

        # Setup routes
        self.app.router.add_get('/healthz', self.healthz)
        self.app.router.add_get('/readyz', self.readyz)
        self.app.router.add_get('/metrics', self.metrics)

    async def start(self):
        """Start the health check server."""
        try:
            self.runner = web.AppRunner(self.app)
            await self.runner.setup()
            self.site = web.TCPSite(self.runner, '0.0.0.0', self.port)
            await self.site.start()
            logger.info(f"Health check server started on port {self.port}")
        except Exception as e:
            logger.error(f"Failed to start health check server: {e}")
            raise

    async def stop(self):
        """Stop the health check server."""
        if self.site:
            await self.site.stop()
        if self.runner:
            await self.runner.cleanup()
        logger.info("Health check server stopped")

    async def healthz(self, request):
        """Liveness probe - checks if the service is running."""
        # Simple liveness check
        if datetime.utcnow() - self.last_health_check > timedelta(minutes=5):
            self.healthy = False

        status = 200 if self.healthy else 503
        response_data = {
            "status": "healthy" if self.healthy else "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "service": "market-data-ingestion"
        }

        return web.Response(
            status=status,
            content_type='application/json',
            text=json.dumps(response_data)
        )

    async def readyz(self, request):
        """Readiness probe - checks if the service is ready to serve traffic."""
        try:
            # Check database connectivity
            if self.writer.pool:
                # Simple query to check DB connection
                async with self.writer.pool.acquire() as conn:
                    await conn.fetchval("SELECT 1")
                ready = True
            else:
                ready = False
        except Exception as e:
            logger.warning(f"Readiness check failed: {e}")
            ready = False

        status = 200 if ready else 503
        response_data = {
            "status": "ready" if ready else "not ready",
            "timestamp": datetime.utcnow().isoformat(),
            "service": "market-data-ingestion",
            "database_connected": ready
        }

        return web.Response(
            status=status,
            content_type='application/json',
            text=json.dumps(response_data)
        )

    async def metrics(self, request):
        """Expose Prometheus metrics."""
        from prometheus_client import generate_latest
        from .metrics import metrics

        return web.Response(
            content_type='text/plain; version=0.0.4; charset=utf-8',
            text=generate_latest(metrics.registry).decode('utf-8')
        )

    def update_health_status(self, healthy: bool):
        """Update the health status."""
        self.healthy = healthy
        self.last_health_check = datetime.utcnow()
