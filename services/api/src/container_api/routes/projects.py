# SPDX-License-Identifier: Apache-2.0
"""Project routes with workspace-level authorization."""

import re
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from container_api.database import get_db
from container_api.dependencies import get_current_user, require_workspace_membership
from container_api.models import Project, User
from container_api.schemas import ProjectCreate, ProjectRead

router = APIRouter(tags=["projects"])


def project_slug(name: str) -> str:
    base = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-") or "project"
    return f"{base}-{uuid4().hex[:6]}"


@router.get("/workspaces/{workspace_id}/projects", response_model=list[ProjectRead])
def list_projects(
    workspace_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[Project]:
    require_workspace_membership(db, user.id, workspace_id)
    statement = (
        select(Project)
        .where(Project.workspace_id == workspace_id)
        .order_by(Project.created_at.desc())
    )
    return list(db.scalars(statement).all())


@router.post(
    "/workspaces/{workspace_id}/projects",
    response_model=ProjectRead,
    status_code=status.HTTP_201_CREATED,
)
def create_project(
    workspace_id: str,
    payload: ProjectCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Project:
    require_workspace_membership(db, user.id, workspace_id)
    project = Project(
        workspace_id=workspace_id,
        created_by=user.id,
        name=payload.name.strip(),
        slug=project_slug(payload.name),
        description=payload.description,
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


@router.get("/projects/{project_id}", response_model=ProjectRead)
def get_project(
    project_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Project:
    project = db.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found.")
    require_workspace_membership(db, user.id, project.workspace_id)
    return project
