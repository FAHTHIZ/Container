# SPDX-License-Identifier: Apache-2.0
"""Workspace routes."""

from uuid import uuid4

from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from container_api.database import get_db
from container_api.dependencies import get_current_user
from container_api.models import User, Workspace, WorkspaceMembership
from container_api.routes.auth import make_slug
from container_api.schemas import WorkspaceCreate, WorkspaceRead

router = APIRouter(prefix="/workspaces", tags=["workspaces"])


@router.get("", response_model=list[WorkspaceRead])
def list_workspaces(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[Workspace]:
    statement = (
        select(Workspace)
        .join(WorkspaceMembership, WorkspaceMembership.workspace_id == Workspace.id)
        .where(WorkspaceMembership.user_id == user.id)
        .order_by(Workspace.created_at)
    )
    return list(db.scalars(statement).all())


@router.post("", response_model=WorkspaceRead, status_code=status.HTTP_201_CREATED)
def create_workspace(
    payload: WorkspaceCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Workspace:
    workspace_id = str(uuid4())
    workspace = Workspace(
        id=workspace_id,
        name=payload.name.strip(),
        slug=make_slug(payload.name),
        created_by=user.id,
    )
    membership = WorkspaceMembership(
        workspace_id=workspace_id,
        user_id=user.id,
        role="owner",
    )
    db.add_all([workspace, membership])
    db.commit()
    db.refresh(workspace)
    return workspace
