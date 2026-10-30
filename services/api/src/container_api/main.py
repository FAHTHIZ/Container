# SPDX-License-Identifier: Apache-2.0
"""Container platform API entry point."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from container_api.config import settings
from container_api.health import router as health_router
from container_api.routes import auth, jobs, projects, workspaces

settings.validate_runtime()

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
    allow_headers=["Authorization", "Content-Type"],
)

app.include_router(health_router)
app.include_router(auth.router, prefix=settings.api_v1_prefix)
app.include_router(workspaces.router, prefix=settings.api_v1_prefix)
app.include_router(projects.router, prefix=settings.api_v1_prefix)
app.include_router(jobs.router, prefix=settings.api_v1_prefix)


@app.get("/", tags=["system"], summary="API information")
def root() -> dict[str, str]:
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "status": "foundation",
        "docs": "/docs",
    }
