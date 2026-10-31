"""Fail CI if exact frozen evaluation questions enter designated training data."""

from __future__ import annotations

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


def find_training_directories(repository_root: Path) -> list[Path]:
    """Find explicitly named training-data roots without following symlinks."""
    found: list[Path] = []
    for current in repository_root.rglob("*"):
        relative_parts = current.relative_to(repository_root).parts
        ignored = any(part in IGNORED_DIRECTORY_NAMES for part in relative_parts)
        if not ignored and current.is_symlink():
            if current.name.lower() in TRAINING_DIRECTORY_NAMES:
                raise QuarantineError(f"Training directory cannot be a symlink: {current}")
        elif not ignored and current.is_dir() and current.name.lower() in TRAINING_DIRECTORY_NAMES:
            found.append(current)
    return sorted(found)


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

    question_bytes = [(question, question.encode("utf-8")) for question in questions]
    files_scanned = 0
    for directory in find_training_directories(root):
        for file_path in directory.rglob("*"):
            if file_path.is_symlink():
                raise QuarantineError(f"Symlink found in training data: {file_path}")
            if file_path.is_dir():
                continue
            if not file_path.is_file():
                raise QuarantineError(f"Unknown filesystem entry in training data: {file_path}")
            if file_path.suffix.lower() not in TEXT_SUFFIXES:
                raise QuarantineError(f"Cannot inspect training file format: {file_path}")
            try:
                data = file_path.read_bytes()
                text_data = data.decode("utf-8", errors="strict")
            except (OSError, UnicodeError) as exc:
                raise QuarantineError(f"Cannot read training file as UTF-8 text: {file_path}") from exc
            for question, _needle in question_bytes:
                if question in text_data:
                    raise QuarantineError(
                        f"Frozen evaluation question leaked into training data: {file_path}"
                    )
            files_scanned += 1
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
