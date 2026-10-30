# SPDX-License-Identifier: Apache-2.0
"""Persistent job submission, monitoring, events, and cancellation."""

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from container_api.database import get_db
from container_api.dependencies import get_current_user, require_workspace_membership
from container_api.models import Job, JobEvent, Project, User
from container_api.schemas import JobCreate, JobEventRead, JobRead

router = APIRouter(tags=["jobs"])


def visible_job(db: Session, user: User, job_id: str) -> Job:
    job = db.get(Job, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found.")
    require_workspace_membership(db, user.id, job.workspace_id)
    return job


@router.get("/projects/{project_id}/jobs", response_model=list[JobRead])
def list_project_jobs(
    project_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[Job]:
    project = db.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found.")
    require_workspace_membership(db, user.id, project.workspace_id)
    statement = (
        select(Job)
        .where(Job.project_id == project_id)
        .order_by(Job.created_at.desc())
    )
    return list(db.scalars(statement).all())


@router.post(
    "/projects/{project_id}/jobs",
    response_model=JobRead,
    status_code=status.HTTP_201_CREATED,
)
def create_job(
    project_id: str,
    payload: JobCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Job:
    project = db.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found.")
    require_workspace_membership(db, user.id, project.workspace_id)

    job = Job(
        workspace_id=project.workspace_id,
        project_id=project.id,
        created_by=user.id,
        kind=payload.kind,
        payload={
            "message": payload.message,
            "delay_seconds": payload.delay_seconds,
        },
        status="queued",
    )
    db.add(job)
    db.flush()
    db.add(JobEvent(job_id=job.id, event_type="job.queued", payload={"kind": job.kind}))
    db.commit()
    db.refresh(job)
    return job


@router.get("/jobs/{job_id}", response_model=JobRead)
def get_job(
    job_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Job:
    return visible_job(db, user, job_id)


@router.get("/jobs/{job_id}/events", response_model=list[JobEventRead])
def list_job_events(
    job_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[JobEvent]:
    visible_job(db, user, job_id)
    return list(
        db.scalars(
            select(JobEvent)
            .where(JobEvent.job_id == job_id)
            .order_by(JobEvent.created_at, JobEvent.id)
        ).all()
    )


@router.post("/jobs/{job_id}/cancel", response_model=JobRead)
def cancel_job(
    job_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Job:
    job = visible_job(db, user, job_id)
    if job.status in {"succeeded", "failed", "cancelled"}:
        raise HTTPException(status_code=409, detail="Job has already finished.")
    if job.status == "queued":
        job.status = "cancelled"
        job.completed_at = datetime.now(UTC)
        db.add(JobEvent(job_id=job.id, event_type="job.cancelled", payload={"phase": "queued"}))
    else:
        job.cancel_requested = True
        db.add(JobEvent(job_id=job.id, event_type="job.cancel_requested", payload={}))
    db.commit()
    db.refresh(job)
    return job
