# SPDX-License-Identifier: Apache-2.0
"""Database-backed worker for demo, eval, and verified external-trainer jobs.

Container supplies job orchestration and provenance checks. It does not contain
a model or a learning algorithm. The train_run adapter is operator-configured
trusted code and must never be selected by a workspace member or job payload.
"""

import logging
import time
from datetime import UTC, datetime

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from container_api.config import settings
from container_api.database import SessionLocal
from container_api.evaluation_jobs import run_eval_job
from container_api.models import Job, JobEvent
from container_api.storage import LocalArtifactStore
from container_api.training_jobs import run_train_job

logger = logging.getLogger("container.worker")


def add_event(db: Session, job_id: str, event_type: str, payload: dict) -> None:
    """Append one durable event to the job history."""
    db.add(JobEvent(job_id=job_id, event_type=event_type, payload=payload))


def finish_cancelled(db: Session, job: Job) -> None:
    """Persist a cancellation after any staged outputs have been discarded."""
    job.status = "cancelled"
    job.completed_at = datetime.now(UTC)
    add_event(db, job.id, "job.cancelled", {"phase": "running"})
    db.commit()


def _remove_staged_files(
    staged_files: list[tuple[LocalArtifactStore, str]],
    *,
    job_id: str,
) -> None:
    """Remove files staged by an uncommitted job transaction."""
    for store, key in staged_files:
        try:
            store.delete(key)
        except (OSError, ValueError):
            logger.exception(
                "Could not remove uncommitted job artifact for job %s",
                job_id,
            )


def process_one_job(db: Session) -> bool:
    """Claim and execute one supported job; return whether a job was claimed."""
    candidate_id = db.scalar(
        select(Job.id)
        .where(Job.status == "queued")
        .order_by(Job.created_at, Job.id)
        .limit(1)
    )
    if candidate_id is None:
        return False

    now = datetime.now(UTC)
    claim = db.execute(
        update(Job)
        .where(Job.id == candidate_id, Job.status == "queued")
        .values(
            status="running",
            started_at=now,
            attempts=Job.attempts + 1,
            updated_at=now,
        )
    )
    if claim.rowcount != 1:
        db.rollback()
        return False

    db.commit()
    job = db.get(Job, candidate_id)
    if job is None:
        return False
    add_event(db, job.id, "job.started", {"worker": "container-worker"})
    db.commit()

    staged_files: list[tuple[LocalArtifactStore, str]] = []
    try:
        if job.kind == "eval_run":
            result, _artifact, store, storage_key = run_eval_job(db, job)
            staged_files.append((store, storage_key))
        elif job.kind == "train_run":
            result, staged_files = run_train_job(db, job)
        elif job.kind in {"demo.echo", "demo.delay"}:
            delay = (
                float(job.payload.get("delay_seconds", 0))
                if job.kind == "demo.delay"
                else 0.0
            )
            steps = max(1, min(20, int(delay * 10))) if delay > 0 else 1
            for step in range(steps):
                if delay > 0:
                    time.sleep(delay / steps)
                db.refresh(job)
                if job.cancel_requested:
                    db.rollback()
                    _remove_staged_files(staged_files, job_id=job.id)
                    cancelled_job = db.get(Job, candidate_id)
                    if cancelled_job is not None:
                        finish_cancelled(db, cancelled_job)
                    return True
                job.progress = min(95, int((step + 1) / steps * 95))
                if step == steps - 1 or job.progress % 25 == 0:
                    add_event(db, job.id, "job.progress", {"progress": job.progress})
                db.commit()

            db.refresh(job)
            if job.cancel_requested:
                db.rollback()
                _remove_staged_files(staged_files, job_id=job.id)
                cancelled_job = db.get(Job, candidate_id)
                if cancelled_job is not None:
                    finish_cancelled(db, cancelled_job)
                return True
            result = {
                "message": str(job.payload.get("message", "")),
                "processed_by": "container-worker",
            }
        else:
            raise ValueError(f"Unsupported worker job kind: {job.kind}")

        db.refresh(job)
        if job.cancel_requested:
            db.rollback()
            _remove_staged_files(staged_files, job_id=job.id)
            cancelled_job = db.get(Job, candidate_id)
            if cancelled_job is not None:
                finish_cancelled(db, cancelled_job)
            return True

        job.result = result
        job.progress = 100
        job.status = "succeeded"
        job.completed_at = datetime.now(UTC)
        event_payload = {"progress": 100, "kind": job.kind}
        if job.kind == "eval_run":
            event_payload["artifact_sha256"] = result["artifact_sha256"]
        elif job.kind == "train_run":
            event_payload["checkpoint_hash"] = result["checkpoint_hash"]
            event_payload["eval_score"] = result["eval_score"]
        add_event(db, job.id, "job.succeeded", event_payload)
        db.commit()
        staged_files.clear()
        logger.info("Completed %s job %s", job.kind, job.id)
        return True
    except Exception as exc:  # noqa: BLE001
        db.rollback()
        _remove_staged_files(staged_files, job_id=candidate_id)
        failed_job = db.get(Job, candidate_id)
        if failed_job is not None:
            failed_job.status = "failed"
            failed_job.error_message = f"{type(exc).__name__}: {str(exc)[:500]}"
            failed_job.completed_at = datetime.now(UTC)
            add_event(db, failed_job.id, "job.failed", {"error": failed_job.error_message})
            db.commit()
        logger.exception("Job %s failed", candidate_id)
        return True


def run_forever() -> None:
    """Poll the durable job table until the process is stopped."""
    logger.info("Container worker started.")
    while True:
        try:
            with SessionLocal() as db:
                processed = process_one_job(db)
        except Exception:  # noqa: BLE001
            logger.exception("Worker polling failed.")
            processed = False
        if not processed:
            time.sleep(max(0.2, settings.worker_poll_seconds))


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run_forever()
