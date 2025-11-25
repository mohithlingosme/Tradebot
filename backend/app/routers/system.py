"""System diagnostics router."""

from fastapi import APIRouter, Query

from ..services.system_service import system_service
from ..schemas.system import LogsResponse, MetricsResponse, StatusResponse

router = APIRouter(prefix="/api", tags=["system"])


@router.get("/status", response_model=StatusResponse)
async def get_status():
    """High-level application status."""
    return await system_service.get_status()


@router.get("/logs", response_model=LogsResponse)
async def get_logs(
    level: str = Query(
        "info",
        pattern="^(debug|info|warning|error|critical)$",
        description="Log level filter",
    ),
    limit: int = Query(25, ge=1, le=200),
):
    """Fetch recent log entries."""
    return await system_service.get_logs(level=level, limit=limit)


@router.get("/metrics", response_model=MetricsResponse)
async def get_metrics():
    """Runtime metrics for dashboarding."""
    return await system_service.get_metrics()
