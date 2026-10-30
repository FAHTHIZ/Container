# SPDX-License-Identifier: Apache-2.0
"""Project-scoped model registry metadata and immutable model versions."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from container_api.database import get_db
from container_api.dependencies import get_current_user, require_workspace_membership
from container_api.models import (
    Artifact,
    ModelVersion,
    Project,
    RegisteredModel,
    User,
)
from container_api.schemas import (
    ModelVersionCreate,
    ModelVersionRead,
    RegisteredModelCreate,
    RegisteredModelRead,
)

router = APIRouter(tags=["model registry"])


def visible_model(db: Session, user: User, model_id: str) -> RegisteredModel:
    model = db.get(RegisteredModel, model_id)
    if model is None:
        raise HTTPException(status_code=404, detail="Model not found.")
    require_workspace_membership(db, user.id, model.workspace_id)
    return model


@router.get(
    "/projects/{project_id}/models",
    response_model=list[RegisteredModelRead],
)
def list_project_models(
    project_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[RegisteredModel]:
    project = db.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found.")
    require_workspace_membership(db, user.id, project.workspace_id)
    statement = (
        select(RegisteredModel)
        .where(RegisteredModel.project_id == project_id)
        .order_by(RegisteredModel.created_at.desc())
    )
    return list(db.scalars(statement).all())


@router.post(
    "/projects/{project_id}/models",
    response_model=RegisteredModelRead,
    status_code=status.HTTP_201_CREATED,
)
def create_project_model(
    project_id: str,
    payload: RegisteredModelCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> RegisteredModel:
    project = db.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found.")
    require_workspace_membership(db, user.id, project.workspace_id)
    model = RegisteredModel(
        workspace_id=project.workspace_id,
        project_id=project.id,
        created_by=user.id,
        name=payload.name.strip(),
        description=payload.description,
        model_family=payload.model_family,
        origin=payload.origin,
    )
    db.add(model)
    try:
        db.commit()
        db.refresh(model)
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A model with that name already exists in this project.",
        ) from exc
    return model


@router.get("/models/{model_id}", response_model=RegisteredModelRead)
def get_model(
    model_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> RegisteredModel:
    return visible_model(db, user, model_id)


@router.get(
    "/models/{model_id}/versions",
    response_model=list[ModelVersionRead],
)
def list_model_versions(
    model_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[ModelVersion]:
    model = visible_model(db, user, model_id)
    statement = (
        select(ModelVersion)
        .where(ModelVersion.model_id == model.id)
        .order_by(ModelVersion.created_at.desc())
    )
    return list(db.scalars(statement).all())


@router.post(
    "/models/{model_id}/versions",
    response_model=ModelVersionRead,
    status_code=status.HTTP_201_CREATED,
)
def create_model_version(
    model_id: str,
    payload: ModelVersionCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ModelVersion:
    model = visible_model(db, user, model_id)
    if payload.artifact_id is not None:
        artifact = db.get(Artifact, payload.artifact_id)
        if artifact is None or artifact.project_id != model.project_id:
            raise HTTPException(
                status_code=404,
                detail="Artifact not found in this model's project.",
            )

    version = ModelVersion(
        model_id=model.id,
        artifact_id=payload.artifact_id,
        created_by=user.id,
        version_label=payload.version_label.strip(),
        format=payload.format,
        quantization=payload.quantization,
        source_uri=payload.source_uri,
        base_model_reference=payload.base_model_reference,
        license_id=payload.license_id,
        details=payload.details,
    )
    db.add(version)
    try:
        db.commit()
        db.refresh(version)
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="That version label already exists for this model.",
        ) from exc
    return version


@router.get(
    "/models/{model_id}/versions/{version_id}",
    response_model=ModelVersionRead,
)
def get_model_version(
    model_id: str,
    version_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ModelVersion:
    model = visible_model(db, user, model_id)
    version = db.get(ModelVersion, version_id)
    if version is None or version.model_id != model.id:
        raise HTTPException(status_code=404, detail="Model version not found.")
    return version
