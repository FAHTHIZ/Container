# SPDX-License-Identifier: Apache-2.0
"""Invoke an operator-owned trainer and verify its loss/checkpoint callback contract.

This module contains no training algorithm. The configured adapter owns all
model-specific learning and must call save_checkpoint at every requested
checkpoint interval while printing a LOSS record at every loss interval.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import shutil
import sys
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from typing import Callable


def _load_adapter(specification: str) -> Callable:
    """Import only the trusted adapter explicitly configured by the operator."""
    module_name, separator, function_name = specification.partition(":")
    if not separator or not module_name or not function_name:
        raise ValueError("Trainer adapter must use module.path:function_name.")
    module = importlib.import_module(module_name)
    adapter = getattr(module, function_name)
    if not callable(adapter):
        raise TypeError("Trainer adapter entry point is not callable.")
    return adapter


def _sha256(path: Path) -> str:
    """Hash the exact bytes in a regular checkpoint file."""
    digest = hashlib.sha256()
    with path.open("rb") as source:
        while chunk := source.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def _save_checkpoint(
    step: int,
    source_value: str | Path,
    *,
    checkpoint_every: int,
    output_dir: Path,
    records: list[dict[str, object]],
) -> None:
    """Copy one adapter checkpoint into the run directory and record its hash."""
    expected_step = (len(records) + 1) * checkpoint_every
    if step != expected_step:
        raise ValueError("Trainer checkpoint callback arrived at an unexpected step.")
    source_argument = Path(source_value)
    if source_argument.is_symlink():
        raise ValueError("Trainer checkpoint source cannot be a symbolic link.")
    source = source_argument.resolve(strict=True)
    if not source.is_file():
        raise ValueError("Trainer checkpoint source must be a regular file.")

    before = source.stat()
    target = output_dir / f"checkpoint-step-{step:08d}.bin"
    if target.exists() or target.is_symlink():
        raise FileExistsError("Generated checkpoint path already exists.")
    shutil.copyfile(source, target)
    after = source.stat()
    if (
        before.st_size != after.st_size
        or before.st_mtime_ns != after.st_mtime_ns
        or before.st_ino != after.st_ino
    ):
        target.unlink(missing_ok=True)
        raise RuntimeError("Trainer checkpoint changed while it was being copied.")

    digest = _sha256(target)
    if len(digest) != 64:
        target.unlink(missing_ok=True)
        raise RuntimeError("Checkpoint hashing did not produce a SHA-256 digest.")
    records.append(
        {
            "step": step,
            "filename": target.name,
            "sha256": digest,
            "size_bytes": target.stat().st_size,
        }
    )


def run_adapter(args: argparse.Namespace) -> None:
    """Run a trusted trainer adapter and write a verified checkpoint manifest."""
    if args.steps % args.loss_every or args.steps % args.checkpoint_every:
        raise ValueError("steps must be divisible by both configured intervals.")

    dataset = Path(args.dataset_path).resolve(strict=True)
    if dataset.is_symlink() or not dataset.is_file():
        raise ValueError("Training dataset must be a regular file.")
    output_dir = Path(args.output_dir).resolve(strict=True)
    if not output_dir.is_dir():
        raise ValueError("Training output directory must already exist.")

    adapter = _load_adapter(args.adapter)
    checkpoints: list[dict[str, object]] = []
    log_buffer = StringIO()

    def save_checkpoint(step: int, path: str | Path) -> None:
        """Callback the adapter must call after it has written each checkpoint."""
        _save_checkpoint(
            step,
            path,
            checkpoint_every=args.checkpoint_every,
            output_dir=output_dir,
            records=checkpoints,
        )

    with redirect_stdout(log_buffer):
        adapter(
            dataset_path=dataset,
            output_dir=output_dir,
            model_id=args.model_id,
            steps=args.steps,
            loss_every=args.loss_every,
            checkpoint_every=args.checkpoint_every,
            save_checkpoint=save_checkpoint,
        )

    expected_steps = list(range(args.checkpoint_every, args.steps + 1, args.checkpoint_every))
    actual_steps = [record["step"] for record in checkpoints]
    if actual_steps != expected_steps:
        raise RuntimeError("Trainer did not save a checkpoint at every requested interval.")

    manifest = {
        "model_id": args.model_id,
        "steps_completed": args.steps,
        "loss_every": args.loss_every,
        "checkpoint_every": args.checkpoint_every,
        "checkpoints": checkpoints,
    }
    manifest_path = output_dir / "manifest.json"
    with manifest_path.open("x", encoding="utf-8") as output:
        json.dump(manifest, output, sort_keys=True)
        output.write("\n")

    # The parent worker validates every LOSS line before accepting the manifest.
    sys.stdout.write(log_buffer.getvalue())
    sys.stdout.flush()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run a trusted external training adapter.")
    parser.add_argument("--adapter", required=True)
    parser.add_argument("--model-id", required=True)
    parser.add_argument("--dataset-path", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--steps", required=True, type=int)
    parser.add_argument("--loss-every", required=True, type=int)
    parser.add_argument("--checkpoint-every", required=True, type=int)
    args = parser.parse_args(argv)

    try:
        run_adapter(args)
    except Exception:
        print(
            "Training adapter failed its execution or checkpoint contract.",
            file=sys.stderr,
        )
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
