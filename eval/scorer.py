"""Deterministic exact-match scoring. No sampling and no model-as-judge."""

from collections.abc import Callable, Sequence
from dataclasses import dataclass


@dataclass(frozen=True)
class Score:
    """A repeatable aggregate score for one frozen evaluation set."""

    correct: int
    n_tasks: int
    score: float


def score_predictions(
    tasks: Sequence[dict[str, str]],
    predict: Callable[[str], str],
) -> Score:
    """Run a prediction function and calculate exact-match accuracy.

    Whitespace at the edges is ignored; case and all interior characters remain
    significant. A predictor exception or non-string result is a hard failure.
    """
    if not tasks:
        raise ValueError("Cannot score an empty evaluation set.")

    correct = 0
    for task in tasks:
        prediction = predict(task["question"])
        if not isinstance(prediction, str):
            raise TypeError(f"Predictor returned a non-string for task {task['id']}.")
        if prediction.strip() == task["expected"].strip():
            correct += 1

    count = len(tasks)
    return Score(correct=correct, n_tasks=count, score=correct / count)
