"""Health endpoint router."""

from fastapi import APIRouter

from ..schemas.health import HealthResponse

router = APIRouter(prefix="/api/health", tags=["health"])


@router.get("", response_model=HealthResponse)
async def health_check():
    """Lightweight liveness probe."""
    return HealthResponse(status="ok")
