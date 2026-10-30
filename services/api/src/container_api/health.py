"""Health endpoints used by local development and deployment probes."""

from fastapi import APIRouter

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/live", summary="Liveness probe")
async def liveness() -> dict[str, str]:
    """Return success when the API process is responding."""
    return {"status": "alive"}


@router.get("/ready", summary="Readiness probe")
async def readiness() -> dict[str, str]:
    """Return success when the API can accept basic requests.

    Database and queue dependency checks will be added with those integrations.
    """
    return {"status": "ready"}
