# SPDX-License-Identifier: Apache-2.0
"""Run the frozen evaluation as a bounded worker subprocess and store its report."""

from __future__ import annotations

import json
import math
import os
import re
import subprocess
import sys
from io import BytesIO
from pathlib import Path, PurePosixPath
from uuid import uuid4

from sqlalchemy.orm import Session

from container_api.config import settings
from container_api.models import Artifact, Job, RegisteredModel
from container_api.storage import LocalArtifactStore

_SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")
_MAX_REPORT_BYTES = 64 * 1024


def _repository_root() -> Path:
    """Find the checkout root in both the source tree and the worker image."""
    for candidate in Path(__file__).resolve().parents:
        if (candidate / "eval" / "runner.py").is_file():
            return candidate
    raise RuntimeError("Frozen evaluation package is not installed in the worker image.")


def _resolve_eval_file(repository_root: Path, requested_path: str) -> tuple[Path, Path]:
    """Allow only regular JSONL files within the repository's eval directory."""
    if not requested_path or "\\" in requested_path:
        raise ValueError("Evaluation path must be a relative repository path.")

    relative = PurePosixPath(requested_path)
    if (
        relative.is_absolute()
        or not relative.parts
        or relative.parts[0] != "eval"
        or any(part in {"", ".", ".."} for part in relative.parts)
        or relative.suffix.lower() != ".jsonl"
    ):
        raise ValueError("Evaluation path must identify a JSONL file inside eval/.")

    eval_root = repository_root / "eval"
    if eval_root.is_symlink() or not eval_root.is_dir():
        raise ValueError("Evaluation directory is unavailable or unsafe.")

    candidate = repository_root
    for part in relative.parts:
        candidate = candidate / part
        if candidate.is_symlink():
            raise ValueError("Symbolic links are not allowed in evaluation paths.")

    try:
        resolved_file = candidate.resolve(strict=True)
        resolved_root = eval_root.resolve(strict=True)
        if not resolved_file.is_relative_to(resolved_root) or not resolved_file.is_file():
            raise ValueError("Evaluation file is outside the permitted directory.")
        hash_file = resolved_file.with_suffix(".sha256")
        if hash_file.is_symlink() or not hash_file.is_file():
            raise ValueError("Evaluation SHA-256 pin is missing or unsafe.")
        if not hash_file.resolve(strict=True).is_relative_to(resolved_root):
            raise ValueError("Evaluation SHA-256 pin is outside the permitted directory.")
    except OSError as exc:
        raise ValueError("Evaluation file or SHA-256 pin is unavailable.") from exc

    return resolved_file, hash_file


def _predictor_environment(repository_root: Path, model_id: str) -> dict[str, str]:
    """Pass only non-secret runtime settings to the trusted predictor process."""
    environment = {
        "PATH": os.environ.get("PATH", ""),
        "PYTHONPATH": str(repository_root),
        "PYTHONIOENCODING": "utf-8",
        "CONTAINER_EVAL_MODEL_ID": model_id,
    }
    for name in ("SYSTEMROOT", "WINDIR", "TEMP", "TMP"):
        value = os.environ.get(name)
        if value:
            environment[name] = value
    return environment


def _validate_eval_result(
    value: object,
    *,
    model_id: str,
    eval_hash: str,
) -> dict[str, object]:
    """Reject malformed, mismatched, or non-finite evaluation output."""
    if not isinstance(value, dict):
        raise RuntimeError("Evaluation process returned an invalid result object.")

    score = value.get("score")
    task_count = value.get("n_tasks")
    if (
        isinstance(score, bool)
        or not isinstance(score, (int, float))
        or not math.isfinite(float(score))
        or not 0 <= float(score) <= 1
    ):
        raise RuntimeError("Evaluation process returned an invalid score.")
    if isinstance(task_count, bool) or not isinstance(task_count, int) or task_count < 1:
        raise RuntimeError("Evaluation process returned an invalid task count.")
    if value.get("model_id") != model_id or value.get("eval_hash") != eval_hash:
        raise RuntimeError("Evaluation process returned mismatched model or eval identity.")
    timestamp = value.get("timestamp")
    if not isinstance(timestamp, str) or not timestamp:
        raise RuntimeError("Evaluation process did not return a timestamp.")

    return {
        "score": float(score),
        "n_tasks": task_count,
        "eval_hash": eval_hash,
        "model_id": model_id,
        "timestamp": timestamp,
    }


def run_eval_job(
    db: Session,
    job: Job,
) -> tuple[dict[str, object], Artifact, LocalArtifactStore, str]:
    """Run one trusted adapter against the pinned eval and stage its report artifact.

    The caller owns the transaction that commits the artifact row and job result.
    If that transaction fails, it must delete the staged storage key.
    """
    if not settings.eval_predictor:
        raise RuntimeError("No trusted evaluation predictor adapter is configured.")

    model_id = job.payload.get("model_id")
    requested_path = job.payload.get("eval_path")
    eval_hash = job.payload.get("eval_hash")
    if not isinstance(model_id, str) or not model_id:
        raise ValueError("Evaluation job is missing model_id.")
    if not isinstance(requested_path, str):
        raise ValueError("Evaluation job is missing eval_path.")
    if not isinstance(eval_hash, str) or not _SHA256_PATTERN.fullmatch(eval_hash):
        raise ValueError("Evaluation job has an invalid eval_hash.")

    model = db.get(RegisteredModel, model_id)
    if model is None or model.project_id != job.project_id:
        raise ValueError("Evaluation model does not belong to this project.")

    repository_root = _repository_root()
    eval_file, hash_file = _resolve_eval_file(repository_root, requested_path)
    command = [
        sys.executable,
        "-m",
        "eval.runner",
        "--model-id",
        model_id,
        "--predictor",
        settings.eval_predictor,
        "--eval-path",
        str(eval_file),
        "--hash-path",
        str(hash_file),
        "--expected-hash",
        eval_hash,
    ]
    try:
        completed = subprocess.run(
            command,
            cwd=repository_root,
            env=_predictor_environment(repository_root, model_id),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
            timeout=settings.eval_timeout_seconds,
        )
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError("Evaluation subprocess exceeded its configured time limit.") from exc
    except OSError as exc:
        raise RuntimeError("Evaluation subprocess could not be started.") from exc

    if completed.returncode != 0:
        # Do not forward child stderr: adapters may accidentally print sensitive material.
        raise RuntimeError(
            f"Evaluation subprocess failed with exit code {completed.returncode}."
        )
    if len(completed.stdout.encode("utf-8")) > _MAX_REPORT_BYTES:
        raise RuntimeError("Evaluation subprocess output exceeded the report size limit.")
    try:
        raw_result = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError("Evaluation subprocess did not return valid JSON.") from exc

    result = _validate_eval_result(raw_result, model_id=model_id, eval_hash=eval_hash)
    report_bytes = (json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n").encode(
        "utf-8"
    )
    store = LocalArtifactStore(settings.artifacts_path)
    storage_key = f"{job.workspace_id}/{job.project_id}/{uuid4().hex}.json"

    try:
        stored = store.put(
            storage_key,
            BytesIO(report_bytes),
            max_bytes=settings.max_artifact_bytes,
        )
        artifact = Artifact(
            workspace_id=job.workspace_id,
            project_id=job.project_id,
            uploaded_by=job.created_by,
            filename=f"evaluation-{job.id}.json",
            media_type="application/json",
            size_bytes=stored.size_bytes,
            sha256=stored.sha256,
            storage_key=stored.key,
        )
        db.add(artifact)
        db.flush()
    except Exception:
        store.delete(storage_key)
        raise

    result["artifact_id"] = artifact.id
    result["artifact_sha256"] = stored.sha256
    return result, artifact, store, storage_key
