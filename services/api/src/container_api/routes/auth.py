# SPDX-License-Identifier: Apache-2.0
"""Registration, login, and current-user routes."""

import re
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from container_api.database import get_db
from container_api.dependencies import get_current_user
from container_api.models import User, Workspace, WorkspaceMembership
from container_api.schemas import LoginRequest, RegisterRequest, TokenRead, UserRead
from container_api.security import create_access_token, hash_password, verify_password

router = APIRouter(prefix="/auth", tags=["authentication"])


def make_slug(value: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return f"{normalized or 'workspace'}-{uuid4().hex[:6]}"


@router.post("/register", response_model=TokenRead, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, db: Session = Depends(get_db)) -> TokenRead:
    email = str(payload.email).lower()
    user_id = str(uuid4())
    workspace_id = str(uuid4())
    user = User(
        id=user_id,
        email=email,
        password_hash=hash_password(payload.password.get_secret_value()),
        display_name=payload.display_name.strip(),
    )
    workspace = Workspace(
        id=workspace_id,
        name=payload.workspace_name.strip(),
        slug=make_slug(payload.workspace_name),
        created_by=user_id,
    )
    membership = WorkspaceMembership(
        workspace_id=workspace_id,
        user_id=user_id,
        role="owner",
    )
    db.add_all([user, workspace, membership])
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with that email already exists.",
        ) from exc
    token, ttl = create_access_token(user_id)
    return TokenRead(access_token=token, expires_in=ttl)


@router.post("/login", response_model=TokenRead)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenRead:
    user = db.scalar(select(User).where(User.email == str(payload.email).lower()))
    if (
        user is None
        or not user.is_active
        or not verify_password(payload.password.get_secret_value(), user.password_hash)
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token, ttl = create_access_token(user.id)
    return TokenRead(access_token=token, expires_in=ttl)


@router.get("/me", response_model=UserRead)
def read_current_user(user: User = Depends(get_current_user)) -> User:
    return user
