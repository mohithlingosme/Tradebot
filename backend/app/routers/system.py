"""System diagnostics router."""

from datetime import datetime
import logging

from fastapi import APIRouter, Depends, HTTPException, Query

from ..core.dependencies import get_current_admin_user
from ..managers.logging_manager import LogAccessError
from ..schemas.user import UserPublic
from ..services.system_service import system_service
from ..schemas.system import LogsResponse, MetricsResponse, StatusResponse

router = APIRouter(prefix="/api", tags=["system"])
logger = logging.getLogger(__name__)


@router.get("/status", response_model=StatusResponse)
async def get_status():
    """High-level application status."""
    return await system_service.get_status()


@router.get("/logs", response_model=LogsResponse)
async def get_logs(
    level: str = Query(
        "INFO",
        pattern="^(?i:debug|info|warning|error|critical)$",
        description="Minimum log level to include",
    ),
    limit: int = Query(
        100,
        ge=1,
        le=500,
        description="Maximum number of log entries to return (newest first)",
    ),
    since: datetime | None = Query(
        None, description="Return entries logged at or after this ISO8601 timestamp"
    ),
    until: datetime | None = Query(
        None, description="Return entries logged at or before this ISO8601 timestamp"
    ),
    _: UserPublic = Depends(get_current_admin_user),
):
    """Fetch recent structured log entries with optional filters."""
    if since and until and since > until:
        raise HTTPException(
            status_code=400, detail="`since` must be earlier than or equal to `until`"
        )
    try:
        return await system_service.get_logs(
            level=level,
            limit=limit,
            since=since,
            until=until,
        )
    except LogAccessError as err:
        logger.error("Failed to retrieve logs: %s", err)
        raise HTTPException(status_code=500, detail="Unable to access log store")


@router.get("/metrics", response_model=MetricsResponse)
async def get_metrics(_: UserPublic = Depends(get_current_admin_user)):
    """Runtime metrics for dashboarding."""
    return await system_service.get_metrics()
