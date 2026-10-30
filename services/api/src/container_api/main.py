# SPDX-License-Identifier: Apache-2.0
"""Container platform API entry point."""

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from container_api.config import settings
from container_api.health import router as health_router
from container_api.routes import (
    artifacts,
    auth,
    chat,
    capabilities,
    jobs,
    model_registry,
    model_sources,
    projects,
    workspaces,
)

settings.validate_runtime()
STATIC_DIR = Path(__file__).parent / "static"

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Control plane for Container workspaces, projects, and jobs.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PATCH", "DELETE"],
    allow_headers=["Authorization", "Content-Type", "Last-Event-ID"],
)

app.mount(
    "/studio-assets",
    StaticFiles(directory=STATIC_DIR),
    name="studio-assets",
)

app.include_router(health_router)
app.include_router(auth.router, prefix=settings.api_v1_prefix)
app.include_router(workspaces.router, prefix=settings.api_v1_prefix)
app.include_router(projects.router, prefix=settings.api_v1_prefix)
app.include_router(jobs.router, prefix=settings.api_v1_prefix)
app.include_router(artifacts.router, prefix=settings.api_v1_prefix)
app.include_router(model_registry.router, prefix=settings.api_v1_prefix)
app.include_router(chat.router, prefix=settings.api_v1_prefix)
app.include_router(capabilities.router, prefix=settings.api_v1_prefix)
app.include_router(model_sources.router, prefix=settings.api_v1_prefix)


@app.get("/", tags=["system"], summary="API information")
def root() -> dict[str, str]:
    """Return basic service metadata without exposing runtime secrets."""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "status": "foundation",
        "studio": "/studio",
        "docs": "/docs",
    }


@app.get("/manifest.webmanifest", include_in_schema=False)
def pwa_manifest() -> FileResponse:
    """Serve the installable web-app manifest."""
    return FileResponse(STATIC_DIR / "manifest.webmanifest", media_type="application/manifest+json")


@app.get("/sw.js", include_in_schema=False)
def service_worker() -> FileResponse:
    """Serve a root-scoped service worker for the static application shell."""
    return FileResponse(
        STATIC_DIR / "sw.js",
        media_type="application/javascript",
        headers={"Cache-Control": "no-cache"},
    )


@app.get("/studio", include_in_schema=False)
def studio() -> FileResponse:
    """Serve the first-party Container Studio."""
    return FileResponse(STATIC_DIR / "index.html")
