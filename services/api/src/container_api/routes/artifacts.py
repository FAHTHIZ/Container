# SPDX-License-Identifier: Apache-2.0
"""Project artifact upload/download routes with workspace authorization."""

from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from container_api.config import settings
from container_api.database import get_db
from container_api.dependencies import get_current_user, require_workspace_membership
from container_api.models import Artifact, Project, User
from container_api.schemas import ArtifactRead
from container_api.storage import LocalArtifactStore

router = APIRouter(tags=["artifacts"])
artifact_store = LocalArtifactStore(settings.artifacts_path)


def safe_filename(filename: str | None) -> str:
    """Keep a display-only basename and strip control characters."""
    name = (filename or "upload.bin").replace("\\", "/").split("/")[-1]
    name = "".join(char for char in name if char.isprintable() and char not in "\r\n")
    name = name.strip().strip(".")
    if not name or name in {".", ".."}:
        name = "upload.bin"
    return name[:255]


def visible_artifact(db: Session, user: User, artifact_id: str) -> Artifact:
    artifact = db.get(Artifact, artifact_id)
    if artifact is None:
        raise HTTPException(status_code=404, detail="Artifact not found.")
    require_workspace_membership(db, user.id, artifact.workspace_id)
    return artifact


@router.get("/projects/{project_id}/artifacts", response_model=list[ArtifactRead])
def list_project_artifacts(
    project_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[Artifact]:
    project = db.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found.")
    require_workspace_membership(db, user.id, project.workspace_id)
    statement = (
        select(Artifact)
        .where(Artifact.project_id == project_id)
        .order_by(Artifact.created_at.desc())
    )
    return list(db.scalars(statement).all())


@router.post(
    "/projects/{project_id}/artifacts",
    response_model=ArtifactRead,
    status_code=status.HTTP_201_CREATED,
)
def upload_project_artifact(
    project_id: str,
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Artifact:
    project = db.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found.")
    require_workspace_membership(db, user.id, project.workspace_id)

    storage_key = f"{project.workspace_id}/{project.id}/{uuid4().hex}.blob"
    try:
        stored = artifact_store.put(
            storage_key,
            file.file,
            max_bytes=settings.max_artifact_bytes,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            detail=f"Artifact exceeds the {settings.max_artifact_bytes}-byte upload limit.",
        ) from exc
    except OSError as exc:
        raise HTTPException(status_code=507, detail="Artifact storage is unavailable.") from exc
    finally:
        file.file.close()

    artifact = Artifact(
        workspace_id=project.workspace_id,
        project_id=project.id,
        uploaded_by=user.id,
        filename=safe_filename(file.filename),
        media_type=(file.content_type or "application/octet-stream")[:255],
        size_bytes=stored.size_bytes,
        sha256=stored.sha256,
        storage_key=stored.key,
    )
    db.add(artifact)
    try:
        db.commit()
        db.refresh(artifact)
    except SQLAlchemyError as exc:
        db.rollback()
        artifact_store.delete(stored.key)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Artifact metadata could not be saved.",
        ) from exc
    return artifact


@router.get("/artifacts/{artifact_id}/download")
def download_artifact(
    artifact_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> FileResponse:
    artifact = visible_artifact(db, user, artifact_id)
    try:
        path = artifact_store.get_path(artifact.storage_key)
    except (ValueError, FileNotFoundError) as exc:
        raise HTTPException(status_code=404, detail="Artifact file is unavailable.") from exc
    return FileResponse(
        path=path,
        media_type=artifact.media_type,
        filename=artifact.filename,
        headers={"X-Content-Type-Options": "nosniff"},
    )
