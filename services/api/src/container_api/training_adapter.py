# SPDX-License-Identifier: Apache-2.0
"""Invoke a trusted external trainer adapter; Container supplies no learning algorithm."""

from __future__ import annotations

import argparse
import importlib
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any


def load_adapter(specification: str) -> Callable[..., Any]:
    """Load the module/function selected by an operator, never by a job payload."""
    module_name, separator, function_name = specification.partition(":")
    if not separator or not module_name or not function_name:
        raise ValueError("Trainer adapter must use module.path:function_name.")
    module = importlib.import_module(module_name)
    adapter = getattr(module, function_name)
    if not callable(adapter):
        raise TypeError("Trainer adapter entry point is not callable.")
    return adapter


def run_adapter(args: argparse.Namespace) -> None:
    """Call the external adapter with immutable inputs and a private output folder."""
    dataset_path = args.dataset_path.resolve(strict=True)
    if dataset_path.is_symlink() or not dataset_path.is_file():
        raise ValueError("Training dataset must be a regular file.")

    output_dir = args.output_dir.resolve(strict=True)
    if output_dir.is_symlink() or not output_dir.is_dir():
        raise ValueError("Training output must be a regular directory.")
    if any(output_dir.iterdir()):
        raise ValueError("Training output directory must start empty.")

    adapter = load_adapter(args.adapter)
    # The adapter owns all learning logic. Its contract is intentionally small:
    # print one LOSS line per loss interval and create one checkpoint file per
    # checkpoint interval using the exact filename documented in TRAINING.md.
    adapter(
        dataset_path=dataset_path,
        output_dir=output_dir,
        model_id=args.model_id,
        steps=args.steps,
        loss_every=args.loss_every,
        checkpoint_every=args.checkpoint_every,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run an operator-configured external trainer adapter."
    )
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
    except Exception as exc:
        print(
            f"Trainer adapter failed: {type(exc).__name__}: {str(exc)[:300]}",
            file=sys.stderr,
        )
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
