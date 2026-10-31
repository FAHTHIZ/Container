"""Fail CI if exact frozen evaluation questions enter designated training data."""

from __future__ import annotations

import os
import sys
from pathlib import Path

from eval.runner import DEFAULT_EVAL_PATH, DEFAULT_HASH_PATH, EvaluationError, load_eval_set

TRAINING_DIRECTORY_NAMES = {
    "train",
    "training",
    "train_data",
    "training_data",
    "train-data",
    "training-data",
}
IGNORED_DIRECTORY_NAMES = {".git", ".venv", "node_modules", "__pycache__", ".pytest_cache"}
TEXT_SUFFIXES = {".txt", ".md", ".json", ".jsonl", ".csv", ".tsv", ".yaml", ".yml"}


class QuarantineError(RuntimeError):
    """Raised when training data cannot be confidently checked for eval leakage."""


def _raise_walk_error(error: OSError) -> None:
    """Convert directory traversal failures into a hard quarantine failure."""
    raise QuarantineError("Cannot inspect every directory in the training-data scan.") from error


def find_training_directories(repository_root: Path) -> list[Path]:
    """Find explicitly named training-data roots without following symlinks."""
    found: list[Path] = []
    for current, directory_names, _file_names in os.walk(
        repository_root,
        topdown=True,
        followlinks=False,
        onerror=_raise_walk_error,
    ):
        current_path = Path(current)
        for name in list(directory_names):
            candidate = current_path / name
            if name in IGNORED_DIRECTORY_NAMES:
                directory_names.remove(name)
            elif candidate.is_symlink():
                if name.lower() in TRAINING_DIRECTORY_NAMES:
                    raise QuarantineError(f"Training directory cannot be a symlink: {candidate}")
                directory_names.remove(name)
            elif name.lower() in TRAINING_DIRECTORY_NAMES:
                found.append(candidate)
    return sorted(found)


def _scan_training_directory(directory: Path, needles: list[str]) -> int:
    """Inspect every file in one training tree; reject symlinks and unknown formats."""
    files_scanned = 0
    for current, directory_names, file_names in os.walk(
        directory,
        topdown=True,
        followlinks=False,
        onerror=_raise_walk_error,
    ):
        current_path = Path(current)
        for name in directory_names:
            candidate = current_path / name
            if candidate.is_symlink():
                raise QuarantineError(f"Symlink found in training data: {candidate}")

        for name in file_names:
            file_path = current_path / name
            if file_path.is_symlink() or not file_path.is_file():
                raise QuarantineError(f"Training entry is not a regular file: {file_path}")
            if file_path.suffix.lower() not in TEXT_SUFFIXES:
                raise QuarantineError(f"Cannot inspect training file format: {file_path}")
            try:
                text_data = file_path.read_text(encoding="utf-8", errors="strict")
            except (OSError, UnicodeError) as exc:
                raise QuarantineError(
                    f"Cannot read training file as UTF-8 text: {file_path}"
                ) from exc
            for question in needles:
                if question in text_data:
                    raise QuarantineError(
                        f"Frozen evaluation question leaked into training data: {file_path}"
                    )
            files_scanned += 1
    return files_scanned


def check_training_data(
    repository_root: str | Path,
    questions: list[str] | None = None,
) -> int:
    """Scan designated training trees; reject unknown formats and unreadable files."""
    root = Path(repository_root).resolve(strict=True)
    if questions is None:
        tasks, _ = load_eval_set(DEFAULT_EVAL_PATH, DEFAULT_HASH_PATH)
        questions = [task["question"] for task in tasks]
    if not questions or any(
        not isinstance(question, str) or not question for question in questions
    ):
        raise QuarantineError("Evaluation questions are missing or invalid.")

    files_scanned = 0
    for directory in find_training_directories(root):
        files_scanned += _scan_training_directory(directory, questions)
    return files_scanned


def main() -> int:
    try:
        count = check_training_data(Path(__file__).resolve().parents[1])
    except (EvaluationError, QuarantineError, OSError, ValueError) as exc:
        print(f"eval quarantine check failed: {exc}", file=sys.stderr)
        return 1
    print(f"eval quarantine check passed; text training files scanned: {count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
