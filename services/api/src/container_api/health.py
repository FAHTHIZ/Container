# SPDX-License-Identifier: Apache-2.0
"""Liveness and dependency-aware readiness endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from container_api.database import get_db

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/live", summary="Liveness probe")
def liveness() -> dict[str, str]:
    return {"status": "alive"}


@router.get("/ready", summary="Readiness probe")
def readiness(db: Session = Depends(get_db)) -> dict[str, str]:
    try:
        db.execute(text("SELECT 1"))
    except SQLAlchemyError as exc:
        raise HTTPException(status_code=503, detail="Database is unavailable.") from exc
    return {"status": "ready", "database": "reachable"}
