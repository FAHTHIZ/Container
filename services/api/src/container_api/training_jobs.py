# SPDX-License-Identifier: Apache-2.0
"""Orchestrate an external trainer, hash its checkpoints, and evaluate the final one.

Container deliberately contains no learning algorithm. The configured adapter
owns model-specific training; this module enforces the job contract, preserves
checkpoint bytes, and records the frozen evaluation result.
"""

from __future__ import annotations

import hashlib
import math
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from uuid import uuid4

from sqlalchemy.orm import Session

from eval.runner import load_eval_set
from container_api.config import settings
from container_api.evaluation_jobs import _repository_root, _resolve_eval_file, run_eval_job
from container_api.models import Artifact, Job, ModelVersion, RegisteredModel
from container_api.storage import LocalArtifactStore

_LOSS_LINE = re.compile(
    r"^LOSS step=(\d+) loss=(-?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?)$"
)
_MAX_TRAIN_LOG_BYTES = 4 * 1024 * 1024
_TEXT_DATA_SUFFIXES = {".txt", ".md", ".json", ".jsonl", ".csv", ".tsv", ".yaml", ".yml"}


def _sha256_file(path: Path) -> str:
    """Calculate the digest of one file without loading it all into memory."""
    digest = hashlib.sha256()
    with path.open("rb") as source:
        while chunk := source.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def _read_frozen_eval(
    repository_root: Path,
    eval_path: str,
    expected_hash: str,
) -> tuple[list[dict[str, str]], str]:
    """Verify the frozen dataset hash before using any question for leakage checks."""
    data_path, hash_path = _resolve_eval_file(repository_root, eval_path)
    tasks, actual_hash = load_eval_set(
        data_path,
        hash_path,
        expected_hash=expected_hash,
    )
    return tasks, actual_hash


def _read_training_dataset(
    store: LocalArtifactStore,
    dataset: Artifact,
    eval_tasks: list[dict[str, str]],
) -> bytes:
    """Verify the uploaded dataset and reject exact frozen-eval question leakage."""
    if Path(dataset.filename).suffix.lower() not in _TEXT_DATA_SUFFIXES:
        raise ValueError("Training dataset must be a supported UTF-8 text file.")

    dataset_path = store.get_path(dataset.storage_key)
    if dataset_path.stat().st_size != dataset.size_bytes:
        raise ValueError("Training dataset size does not match artifact metadata.")

    content = dataset_path.read_bytes()
    if hashlib.sha256(content).hexdigest() != dataset.sha256:
        raise ValueError("Training dataset SHA-256 does not match artifact metadata.")

    try:
        text = content.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise ValueError("Training dataset must be valid UTF-8 text.") from exc

    for task in eval_tasks:
        if task["question"] in text:
            raise ValueError("Training dataset contains a frozen evaluation question.")
    return content


def _trainer_environment(repository_root: Path) -> dict[str, str]:
    """Pass only runtime variables needed by a trusted adapter, not API secrets."""
    paths = [
        repository_root,
        repository_root / "services" / "api" / "src",
        repository_root / "services" / "api" / "tests",
    ]
    environment = {
        "PATH": os.environ.get("PATH", ""),
        "PYTHONPATH": os.pathsep.join(str(path) for path in paths),
        "PYTHONIOENCODING": "utf-8",
    }
    for name in ("CUDA_VISIBLE_DEVICES", "LD_LIBRARY_PATH", "SYSTEMROOT", "WINDIR"):
        value = os.environ.get(name)
        if value:
            environment[name] = value
    return environment


def _parse_loss_log(
    stdout: str,
    *,
    steps: int,
    loss_every: int,
) -> list[dict[str, int | float]]:
    """Require one finite LOSS record at every configured interval."""
    if len(stdout.encode("utf-8")) > _MAX_TRAIN_LOG_BYTES:
        raise RuntimeError("Trainer output exceeded the configured log size limit.")

    losses: dict[int, float] = {}
    for line in stdout.splitlines():
        if not line.startswith("LOSS"):
            continue
        match = _LOSS_LINE.fullmatch(line)
        if match is None:
            raise RuntimeError("Trainer emitted a malformed LOSS record.")

        step = int(match.group(1))
        loss_value = float(match.group(2))
        if (
            step < 1
            or step > steps
            or step % loss_every != 0
            or step in losses
            or not math.isfinite(loss_value)
        ):
            raise RuntimeError("Trainer emitted a duplicate, mistimed, or invalid loss record.")
        losses[step] = loss_value

    expected_steps = list(range(loss_every, steps + 1, loss_every))
    if sorted(losses) != expected_steps:
        raise RuntimeError("Trainer did not print loss at every requested interval.")
    return [{"step": step, "loss": losses[step]} for step in expected_steps]


def _checkpoint_files(
    output_dir: Path,
    *,
    steps: int,
    checkpoint_every: int,
) -> list[tuple[int, Path, str, int]]:
    """Require exactly the expected checkpoint files and hash their actual bytes."""
    expected_steps = list(range(checkpoint_every, steps + 1, checkpoint_every))
    if not expected_steps:
        raise RuntimeError("Trainer did not have a checkpoint interval within its step budget.")

    expected_names = {
        f"checkpoint-step-{step:08d}.bin": step for step in expected_steps
    }
    actual_entries = list(output_dir.iterdir())
    actual_names: set[str] = set()

    for entry in actual_entries:
        if entry.is_symlink() or not entry.is_file():
            raise RuntimeError("Trainer output contains a non-regular or symbolic-link entry.")
        actual_names.add(entry.name)

    if actual_names != set(expected_names):
        raise RuntimeError("Trainer checkpoint files do not match the requested save intervals.")

    verified: list[tuple[int, Path, str, int]] = []
    for filename, step in expected_names.items():
        path = output_dir / filename
        size_bytes = path.stat().st_size
        if size_bytes < 1 or size_bytes > settings.max_artifact_bytes:
            raise RuntimeError("Trainer checkpoint is empty or exceeds the artifact size limit.")
        digest = _sha256_file(path)
        verified.append((step, path, digest, size_bytes))
    return verified


def run_train_job(
    db: Session,
    job: Job,
) -> tuple[dict[str, object], list[tuple[LocalArtifactStore, str]]]:
    """Run one trusted adapter, store every hashed checkpoint, then evaluate the final one.

    The function does not implement or inspect a learning algorithm. It invokes
    an operator-configured module, validates the declared outputs, and stages
    all files for the worker's database transaction.
    """
    if not settings.train_runner:
        raise RuntimeError("No trusted external trainer adapter is configured.")
    if not settings.eval_predictor:
        raise RuntimeError("No trusted frozen-evaluation predictor is configured.")

    payload = job.payload
    model_id = payload.get("model_id")
    dataset_id = payload.get("dataset_artifact_id")
    eval_path = payload.get("eval_path")
    eval_hash = payload.get("eval_hash")
    steps = payload.get("steps")
    loss_every = payload.get("loss_every")
    checkpoint_every = payload.get("checkpoint_every")

    if not isinstance(model_id, str) or not model_id:
        raise ValueError("Training job is missing model_id.")
    if not isinstance(dataset_id, str) or not dataset_id:
        raise ValueError("Training job is missing dataset_artifact_id.")
    if not isinstance(eval_path, str) or not eval_path:
        raise ValueError("Training job is missing eval_path.")
    if not isinstance(eval_hash, str) or re.fullmatch(r"[0-9a-f]{64}", eval_hash) is None:
        raise ValueError("Training job has an invalid eval_hash.")

    numeric_values = (steps, loss_every, checkpoint_every)
    if any(
        isinstance(value, bool) or not isinstance(value, int) or value < 1
        for value in numeric_values
    ):
        raise ValueError("Training steps and save intervals must be positive integers.")
    if steps > 100000 or steps // loss_every > 2000:
        raise ValueError("Training request exceeds the configured step or loss-output limit.")
    if steps // checkpoint_every < 1 or steps // checkpoint_every > 200:
        raise ValueError("Training request must produce between 1 and 200 checkpoints.")

    model = db.get(RegisteredModel, model_id)
    dataset = db.get(Artifact, dataset_id)
    if model is None or model.project_id != job.project_id:
        raise ValueError("Training model does not belong to this project.")
    if dataset is None or dataset.project_id != job.project_id:
        raise ValueError("Training dataset does not belong to this project.")

    repository_root = _repository_root()
    eval_tasks, verified_eval_hash = _read_frozen_eval(
        repository_root,
        eval_path,
        eval_hash,
    )
    artifact_store = LocalArtifactStore(settings.artifacts_path)
    dataset_bytes = _read_training_dataset(artifact_store, dataset, eval_tasks)
    staged_files: list[tuple[LocalArtifactStore, str]] = []

    try:
        with tempfile.TemporaryDirectory(prefix="container-train-") as directory:
            temporary_root = Path(directory)
            dataset_copy = temporary_root / f"dataset{Path(dataset.filename).suffix.lower()}"
            dataset_copy.write_bytes(dataset_bytes)
            dataset_copy.chmod(0o400)

            output_dir = temporary_root / "checkpoints"
            output_dir.mkdir()
            command = [
                sys.executable,
                "-m",
                "container_api.training_adapter",
                "--adapter",
                settings.train_runner,
                "--model-id",
                model_id,
                "--dataset-path",
                str(dataset_copy),
                "--output-dir",
                str(output_dir),
                "--steps",
                str(steps),
                "--loss-every",
                str(loss_every),
                "--checkpoint-every",
                str(checkpoint_every),
            ]
            try:
                completed = subprocess.run(
                    command,
                    cwd=repository_root,
                    env=_trainer_environment(repository_root),
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    check=False,
                    timeout=settings.train_timeout_seconds,
                )
            except subprocess.TimeoutExpired as exc:
                raise RuntimeError("Trainer exceeded its configured time limit.") from exc
            except OSError as exc:
                raise RuntimeError("Trainer subprocess could not be started.") from exc

            if completed.returncode != 0:
                raise RuntimeError(
                    f"Trainer adapter failed with exit code {completed.returncode}."
                )
            output_size = (
                len(completed.stdout.encode("utf-8"))
                + len(completed.stderr.encode("utf-8"))
            )
            if output_size > _MAX_TRAIN_LOG_BYTES:
                raise RuntimeError("Trainer output exceeded the configured log size limit.")
            losses = _parse_loss_log(
                completed.stdout,
                steps=steps,
                loss_every=loss_every,
            )
            checkpoints = _checkpoint_files(
                output_dir,
                steps=steps,
                checkpoint_every=checkpoint_every,
            )

            checkpoint_results: list[dict[str, object]] = []
            checkpoint_artifacts: list[Artifact] = []
            for step, checkpoint_path, digest, size_bytes in checkpoints:
                storage_key = (
                    f"{job.workspace_id}/{job.project_id}/"
                    f"{job.id}-checkpoint-{step:08d}-{uuid4().hex}.bin"
                )
                with checkpoint_path.open("rb") as checkpoint_source:
                    stored = artifact_store.put(
                        storage_key,
                        checkpoint_source,
                        max_bytes=settings.max_artifact_bytes,
                    )
                staged_files.append((artifact_store, storage_key))
                if stored.sha256 != digest or stored.size_bytes != size_bytes:
                    raise RuntimeError("Stored checkpoint differs from its verified source bytes.")

                artifact = Artifact(
                    workspace_id=job.workspace_id,
                    project_id=job.project_id,
                    uploaded_by=job.created_by,
                    filename=f"checkpoint-step-{step:08d}.bin",
                    media_type="application/octet-stream",
                    size_bytes=stored.size_bytes,
                    sha256=stored.sha256,
                    storage_key=stored.key,
                )
                db.add(artifact)
                db.flush()
                checkpoint_artifacts.append(artifact)
                checkpoint_results.append(
                    {
                        "step": step,
                        "artifact_id": artifact.id,
                        "checkpoint_hash": stored.sha256,
                        "size_bytes": stored.size_bytes,
                    }
                )

            final_step, final_path, final_hash, _final_size = checkpoints[-1]
            evaluation, _report, report_store, report_key = run_eval_job(
                db,
                job,
                checkpoint_path=final_path,
            )
            staged_files.append((report_store, report_key))

            final_checkpoint = checkpoint_results[-1]
            model_version = ModelVersion(
                model_id=model.id,
                artifact_id=checkpoint_artifacts[-1].id,
                created_by=job.created_by,
                version_label=f"candidate-{job.id[:8]}",
                format="other",
                details={
                    "checkpoint_hash": final_hash,
                    "checkpoint_step": final_step,
                    "eval_score": evaluation["score"],
                    "eval_hash": verified_eval_hash,
                    "n_tasks": evaluation["n_tasks"],
                    "steps_requested": steps,
                },
            )
            db.add(model_version)
            db.flush()

            result: dict[str, object] = {
                "model_id": model_id,
                "dataset_artifact_id": dataset_id,
                "steps_completed": steps,
                "loss_every": loss_every,
                "checkpoint_every": checkpoint_every,
                "loss_records": losses,
                "checkpoints": checkpoint_results,
                "checkpoint_hash": final_checkpoint["checkpoint_hash"],
                "checkpoint_artifact_id": final_checkpoint["artifact_id"],
                "eval_score": evaluation["score"],
                "eval_hash": verified_eval_hash,
                "n_tasks": evaluation["n_tasks"],
                "model_version_id": model_version.id,
                "evaluation_artifact_id": evaluation["artifact_id"],
                "evaluation_artifact_sha256": evaluation["artifact_sha256"],
            }
            return result, staged_files
    except Exception:
        for store, storage_key in staged_files:
            store.delete(storage_key)
        raise
