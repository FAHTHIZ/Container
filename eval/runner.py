"""Run deterministic evaluation against an explicit prediction function."""

from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import re
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Callable

from eval.scorer import Score, score_predictions
from eval.stub_predictor import predict as stub_predict

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_EVAL_PATH = REPOSITORY_ROOT / "eval" / "data" / "eval.jsonl"
DEFAULT_HASH_PATH = REPOSITORY_ROOT / "eval" / "data" / "eval.sha256"
_SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")


class EvaluationError(RuntimeError):
    """Raised when the frozen evaluation input or execution is invalid."""


def load_eval_set(
    eval_path: str | Path = DEFAULT_EVAL_PATH,
    hash_path: str | Path = DEFAULT_HASH_PATH,
    *,
    expected_hash: str | None = None,
) -> tuple[list[dict[str, str]], str]:
    """Verify the frozen file digest before parsing any evaluation tasks."""
    data_path = Path(eval_path)
    digest_path = Path(hash_path)
    try:
        raw = data_path.read_bytes()
        pinned_hash_text = digest_path.read_text(encoding="ascii").strip()
    except (OSError, UnicodeError) as exc:
        raise EvaluationError("Evaluation file or SHA-256 pin is missing or unreadable.") from exc

    if not _SHA256_PATTERN.fullmatch(pinned_hash_text):
        raise EvaluationError(
            "Evaluation SHA-256 pin must contain exactly 64 lowercase hex digits."
        )

    actual_hash = hashlib.sha256(raw).hexdigest()
    if actual_hash != pinned_hash_text:
        raise EvaluationError("Frozen evaluation hash mismatch; refusing to run.")

    if expected_hash is not None:
        if not _SHA256_PATTERN.fullmatch(expected_hash):
            raise EvaluationError("Requested evaluation hash is not a valid SHA-256 digest.")
        if expected_hash != actual_hash:
            raise EvaluationError("Requested evaluation hash does not match the frozen file.")

    try:
        text = raw.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise EvaluationError("Evaluation file must be valid UTF-8.") from exc

    tasks: list[dict[str, str]] = []
    seen_ids: set[str] = set()
    for line_number, line in enumerate(text.splitlines(), start=1):
        if not line.strip():
            raise EvaluationError(f"Blank line in evaluation data at line {line_number}.")
        try:
            item = json.loads(line)
        except json.JSONDecodeError as exc:
            raise EvaluationError(f"Malformed JSON on evaluation line {line_number}.") from exc
        if not isinstance(item, dict) or set(item) != {"id", "question", "expected"}:
            raise EvaluationError(
                f"Evaluation line {line_number} must contain only id, question, and expected."
            )
        if not all(isinstance(item[key], str) and item[key].strip() for key in item):
            raise EvaluationError(
                f"Evaluation line {line_number} has an empty or non-string field."
            )
        if item["id"] in seen_ids:
            raise EvaluationError(f"Duplicate evaluation task ID on line {line_number}.")
        seen_ids.add(item["id"])
        tasks.append(item)

    if not tasks:
        raise EvaluationError("Frozen evaluation set is empty.")
    return tasks, actual_hash


def load_predictor(specification: str) -> Callable[[str], str]:
    """Load a trusted Python callable using the form module.path:function_name."""
    module_name, separator, function_name = specification.partition(":")
    if not separator or not module_name or not function_name:
        raise EvaluationError("Predictor must use module.path:function_name syntax.")
    try:
        module = importlib.import_module(module_name)
        predictor = getattr(module, function_name)
    except (ImportError, AttributeError) as exc:
        raise EvaluationError("Predictor could not be imported.") from exc
    if not callable(predictor):
        raise EvaluationError("Predictor entry point is not callable.")
    return predictor


def run_evaluation(
    tasks: list[dict[str, str]],
    predictor: Callable[[str], str],
) -> Score:
    """Score a predictor and convert all execution errors into hard failures."""
    try:
        return score_predictions(tasks, predictor)
    except Exception as exc:
        raise EvaluationError("Prediction failed; evaluation result is invalid.") from exc


def run_negative_control(tasks: list[dict[str, str]]) -> tuple[Score, Score]:
    """Prove a no-op predictor scores strictly below the known-good test stub."""
    baseline = run_evaluation(tasks, stub_predict)

    def no_op_predict(_question: str) -> str:
        return "__NEGATIVE_CONTROL_NO_ANSWER__"

    control = run_evaluation(tasks, no_op_predict)
    if control.score >= baseline.score:
        raise EvaluationError(
            "Negative control was not worse than the known-good stub; eval is not trusted."
        )
    return control, baseline


def _result_payload(eval_hash: str, model_id: str, score: Score) -> dict[str, object]:
    return {
        "eval_hash": eval_hash,
        "model_id": model_id,
        "score": score.score,
        "n_tasks": score.n_tasks,
        "timestamp": datetime.now(UTC).isoformat(),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run Container's frozen deterministic eval.")
    parser.add_argument("--model-id", default="deterministic-stub")
    parser.add_argument("--predictor", default="eval.stub_predictor:predict")
    parser.add_argument("--eval-path", type=Path, default=DEFAULT_EVAL_PATH)
    parser.add_argument("--hash-path", type=Path, default=DEFAULT_HASH_PATH)
    parser.add_argument("--expected-hash")
    parser.add_argument("--negative-control", action="store_true")
    args = parser.parse_args(argv)

    try:
        tasks, eval_hash = load_eval_set(
            args.eval_path,
            args.hash_path,
            expected_hash=args.expected_hash,
        )
        if args.negative_control:
            control, baseline = run_negative_control(tasks)
            result = _result_payload(eval_hash, "negative-control", control)
            result["negative_control"] = True
            result["negative_control_pass"] = control.score < baseline.score
            result["baseline_score"] = baseline.score
        else:
            predictor = load_predictor(args.predictor)
            score = run_evaluation(tasks, predictor)
            result = _result_payload(eval_hash, args.model_id, score)
        print(json.dumps(result, sort_keys=True))
        return 0
    except EvaluationError as exc:
        print(f"evaluation failed: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
