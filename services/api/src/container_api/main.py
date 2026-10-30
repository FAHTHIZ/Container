"""Container platform API entry point."""

from fastapi import FastAPI

from container_api.config import settings
from container_api.health import router as health_router

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Control plane for Container projects, data, models, and jobs.",
)

app.include_router(health_router)


@app.get("/", tags=["system"], summary="API information")
async def root() -> dict[str, str]:
    """Return basic service metadata without exposing runtime secrets."""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "status": "foundation",
        "docs": "/docs",
    }
