"""Logic for delivering system diagnostics."""

from datetime import datetime

from ..config import settings
from ..managers import LoggingManager, MetricsManager
from ..schemas.system import DependencyHealth, LogsResponse, MetricsResponse, StatusResponse

log_manager = LoggingManager()
metrics_manager = MetricsManager()


class SystemService:
    async def get_status(self) -> StatusResponse:
        probe_time = datetime.utcnow()
        dependencies = {
            "database": True,
            "market_data": True,
            "broker": True,
            "cache": True,
        }
        return StatusResponse(
            app_version=settings.app_name,
            uptime_seconds=4523.2,
            environment=settings.environment,
            dependencies_ok=dependencies,
            dependency_details=[
                DependencyHealth(
                    name=name,
                    healthy=healthy,
                    last_checked=probe_time,
                )
                for name, healthy in dependencies.items()
            ],
        )

    async def get_logs(
        self,
        level: str,
        limit: int,
        since: datetime | None = None,
        until: datetime | None = None,
    ) -> LogsResponse:
        entries = await log_manager.fetch_recent_logs(
            level=level,
            limit=limit,
            since=since,
            until=until,
        )
        return LogsResponse(entries=entries, total=len(entries))

    async def get_metrics(self) -> MetricsResponse:
        return await metrics_manager.gather()


system_service = SystemService()
