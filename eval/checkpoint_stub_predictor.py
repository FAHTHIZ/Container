"""Evaluation fixture that proves a final checkpoint path is supplied to the adapter."""

import os
from pathlib import Path

from eval.stub_predictor import predict as stub_predict


def predict(question: str) -> str:
    """Use fixed test answers only when the expected final checkpoint is present."""
    checkpoint_value = os.environ.get("CONTAINER_EVAL_CHECKPOINT_PATH")
    if not checkpoint_value:
        raise RuntimeError("The evaluation adapter did not receive a checkpoint path.")

    checkpoint = Path(checkpoint_value)
    if checkpoint.is_symlink() or not checkpoint.is_file():
        raise RuntimeError("The evaluation checkpoint is missing or unsafe.")
    if checkpoint.name != "checkpoint-step-00000004.bin":
        raise RuntimeError("The evaluation adapter did not receive the final checkpoint.")
    if not checkpoint.read_bytes():
        raise RuntimeError("The final checkpoint fixture is empty.")

    return stub_predict(question)
