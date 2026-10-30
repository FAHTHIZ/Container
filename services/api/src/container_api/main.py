# SPDX-License-Identifier: Apache-2.0
"""Container platform API entry point."""

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from container_api.config import settings
from container_api.health import router as health_router
from container_api.routes import artifacts, auth, chat, jobs, model_registry, projects, workspaces

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


@app.get("/studio", include_in_schema=False)
def studio() -> FileResponse:
    """Serve the first-party Container Studio."""
    return FileResponse(STATIC_DIR / "index.html")
