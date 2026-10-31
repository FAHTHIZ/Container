# SPDX-License-Identifier: Apache-2.0
"""Persistent job submission, monitoring, events, streaming, and cancellation."""

import asyncio
import json
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy import and_, or_, select
from sqlalchemy.orm import Session

from container_api.config import settings
from container_api.database import SessionLocal, get_db
from container_api.dependencies import get_current_user, require_workspace_membership
from container_api.models import Job, JobEvent, Project, RegisteredModel, User
from container_api.schemas import JobCreate, JobEventRead, JobRead

router = APIRouter(tags=["jobs"])
TERMINAL_JOB_STATES = {"succeeded", "failed", "cancelled"}


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

    if payload.kind in {"eval_run", "train_run"}:
        if not payload.model_id or not payload.eval_path or not payload.eval_hash:
            raise HTTPException(
                status_code=422,
                detail="Evaluation jobs require model_id, eval_path, and eval_hash.",
            )
        registered_model = db.get(RegisteredModel, payload.model_id)
        if registered_model is None or registered_model.project_id != project.id:
            raise HTTPException(status_code=404, detail="Project model not found.")

        if payload.kind == "eval_run":
            if not settings.eval_predictor:
                raise HTTPException(
                    status_code=503,
                    detail="No trusted evaluation predictor adapter is configured on the worker.",
                )
            if (
                payload.dataset_artifact_id is not None
                or payload.steps is not None
                or payload.loss_every is not None
                or payload.checkpoint_every is not None
            ):
                raise HTTPException(
                    status_code=422,
                    detail="Training fields are only valid for train_run jobs.",
                )
            job_payload = {
                "model_id": payload.model_id,
                "eval_path": payload.eval_path,
                "eval_hash": payload.eval_hash,
            }
        else:
            if not settings.train_runner or not settings.eval_predictor:
                raise HTTPException(
                    status_code=503,
                    detail=(
                        "A trusted trainer adapter and evaluation adapter must both be "
                        "configured on the worker."
                    ),
                )
            if (
                not payload.dataset_artifact_id
                or payload.steps is None
                or payload.loss_every is None
                or payload.checkpoint_every is None
            ):
                raise HTTPException(
                    status_code=422,
                    detail=(
                        "train_run requires dataset_artifact_id, steps, loss_every, "
                        "and checkpoint_every."
                    ),
                )
            if payload.steps % payload.loss_every != 0:
                raise HTTPException(
                    status_code=422,
                    detail="steps must be divisible by loss_every so the final loss is recorded.",
                )
            if payload.steps % payload.checkpoint_every != 0:
                raise HTTPException(
                    status_code=422,
                    detail=(
                        "steps must be divisible by checkpoint_every so a final checkpoint "
                        "is available for evaluation."
                    ),
                )
            dataset = db.get(Artifact, payload.dataset_artifact_id)
            if dataset is None or dataset.project_id != project.id:
                raise HTTPException(status_code=404, detail="Training dataset artifact not found.")
            job_payload = {
                "model_id": payload.model_id,
                "dataset_artifact_id": payload.dataset_artifact_id,
                "steps": payload.steps,
                "loss_every": payload.loss_every,
                "checkpoint_every": payload.checkpoint_every,
                "eval_path": payload.eval_path,
                "eval_hash": payload.eval_hash,
            }
    else:
        if any(
            value is not None
            for value in (
                payload.model_id,
                payload.eval_path,
                payload.eval_hash,
                payload.dataset_artifact_id,
                payload.steps,
                payload.loss_every,
                payload.checkpoint_every,
            )
        ):
            raise HTTPException(
                status_code=422,
                detail="Model, evaluation, and training fields require the matching job type.",
            )
        job_payload = {
            "message": payload.message,
            "delay_seconds": payload.delay_seconds,
        }

    job = Job(
        workspace_id=project.workspace_id,
        project_id=project.id,
        created_by=user.id,
        kind=payload.kind,
        payload=job_payload,
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


def read_event_batch(job_id: str, after_id: str | None) -> tuple[list[dict], bool]:
    """Read a bounded event batch and terminal state using a short-lived session."""
    with SessionLocal() as stream_db:
        statement = select(JobEvent).where(JobEvent.job_id == job_id)
        if after_id:
            cursor = stream_db.get(JobEvent, after_id)
            if cursor is None or cursor.job_id != job_id:
                return [], True
            statement = statement.where(
                or_(
                    JobEvent.created_at > cursor.created_at,
                    and_(
                        JobEvent.created_at == cursor.created_at,
                        JobEvent.id > cursor.id,
                    ),
                )
            )
        events = stream_db.scalars(
            statement.order_by(JobEvent.created_at, JobEvent.id).limit(100)
        ).all()
        job = stream_db.get(Job, job_id)
        terminal = job is None or job.status in TERMINAL_JOB_STATES
        batch = [
            {
                "id": event.id,
                "event_type": event.event_type,
                "created_at": event.created_at.isoformat(),
                "payload": event.payload,
            }
            for event in events
        ]
        return batch, terminal


@router.get("/jobs/{job_id}/events/stream")
def stream_job_events(
    job_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    last_event_id: str | None = Header(default=None, alias="Last-Event-ID"),
    after_id: str | None = Query(default=None, max_length=36),
) -> StreamingResponse:
    """Stream authorized job events using Server-Sent Events.

    Reconnect with Last-Event-ID to resume after the last received event.
    """
    visible_job(db, user, job_id)
    cursor_id = last_event_id or after_id
    if cursor_id:
        cursor = db.get(JobEvent, cursor_id)
        if cursor is None or cursor.job_id != job_id:
            raise HTTPException(status_code=400, detail="Invalid job event cursor.")

    async def event_generator():
        current_cursor = cursor_id
        idle_polls = 0
        while True:
            batch, terminal = await asyncio.to_thread(
                read_event_batch, job_id, current_cursor
            )
            if batch:
                for event in batch:
                    yield (
                        f"id: {event['id']}\n"
                        f"event: {event['event_type']}\n"
                        f"data: {json.dumps(event, separators=(',', ':'))}\n\n"
                    )
                    current_cursor = event["id"]
                idle_polls = 0
            elif terminal:
                break
            else:
                idle_polls += 1
                if idle_polls % 20 == 0:
                    yield ": keep-alive\n\n"
                await asyncio.sleep(0.25)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


@router.post("/jobs/{job_id}/cancel", response_model=JobRead)
def cancel_job(
    job_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Job:
    job = visible_job(db, user, job_id)
    if job.status in TERMINAL_JOB_STATES:
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
