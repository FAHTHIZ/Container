# SPDX-License-Identifier: Apache-2.0
"""Database-backed worker for harmless demo tasks and frozen eval jobs.

The database is the source of truth for job state. Conditional status updates
ensure only one worker can claim a queued job. The only job implementations are
demo.echo, demo.delay, and eval_run. Evaluation runs a trusted operator-configured
predictor in a bounded subprocess; it does not train a model or run user code.
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

logger = logging.getLogger("container.worker")


def add_event(db: Session, job_id: str, event_type: str, payload: dict) -> None:
    db.add(JobEvent(job_id=job_id, event_type=event_type, payload=payload))


def finish_cancelled(db: Session, job: Job) -> None:
    job.status = "cancelled"
    job.completed_at = datetime.now(UTC)
    add_event(db, job.id, "job.cancelled", {"phase": "running"})
    db.commit()


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

    cleanup_store = None
    cleanup_key: str | None = None
    try:
        if job.kind == "eval_run":
            result, _artifact, cleanup_store, cleanup_key = run_eval_job(db, job)
            db.refresh(job)
            if job.cancel_requested:
                db.rollback()
                if cleanup_store is not None and cleanup_key is not None:
                    cleanup_store.delete(cleanup_key)
                cancelled_job = db.get(Job, candidate_id)
                if cancelled_job is not None:
                    finish_cancelled(db, cancelled_job)
                return True

            job.result = result
            job.progress = 100
            job.status = "succeeded"
            job.completed_at = datetime.now(UTC)
            add_event(
                db,
                job.id,
                "job.succeeded",
                {
                    "progress": 100,
                    "kind": "eval_run",
                    "artifact_sha256": result["artifact_sha256"],
                },
            )
            db.commit()
            cleanup_store = None
            cleanup_key = None
            logger.info("Completed evaluation job %s", job.id)
            return True

        if job.kind not in {"demo.echo", "demo.delay"}:
            raise ValueError(f"Unsupported worker job kind: {job.kind}")

        delay = float(job.payload.get("delay_seconds", 0)) if job.kind == "demo.delay" else 0
        steps = max(1, min(20, int(delay * 10))) if delay > 0 else 1
        for step in range(steps):
            if delay > 0:
                time.sleep(delay / steps)
            db.refresh(job)
            if job.cancel_requested:
                finish_cancelled(db, job)
                return True
            job.progress = min(95, int((step + 1) / steps * 95))
            if step == steps - 1 or job.progress % 25 == 0:
                add_event(db, job.id, "job.progress", {"progress": job.progress})
            db.commit()

        db.refresh(job)
        if job.cancel_requested:
            finish_cancelled(db, job)
            return True

        job.result = {
            "message": str(job.payload.get("message", "")),
            "processed_by": "container-worker",
        }
        job.progress = 100
        job.status = "succeeded"
        job.completed_at = datetime.now(UTC)
        add_event(db, job.id, "job.succeeded", {"progress": 100})
        db.commit()
        logger.info("Completed job %s", job.id)
        return True
    except Exception as exc:  # noqa: BLE001
        db.rollback()
        if cleanup_store is not None and cleanup_key is not None:
            try:
                cleanup_store.delete(cleanup_key)
            except OSError:
                logger.exception("Could not clean up failed evaluation artifact for job %s", candidate_id)
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
