# SPDX-License-Identifier: Apache-2.0
"""Tests for the frozen evaluation runner and training-data quarantine."""

import json
import subprocess
import sys
from pathlib import Path

import pytest

from eval.check_quarantine import QuarantineError, check_training_data
from eval.runner import EvaluationError, load_eval_set, run_evaluation, run_negative_control
from eval.stub_predictor import predict as stub_predict

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]


def test_frozen_eval_hash_matches_dataset() -> None:
    tasks, digest = load_eval_set()
    assert len(tasks) == 6
    assert len(digest) == 64


def test_eval_hash_mismatch_fails_closed(tmp_path) -> None:
    data_path = tmp_path / "eval.jsonl"
    hash_path = tmp_path / "eval.sha256"
    data_path.write_text(
        '{"id":"one","question":"Question?","expected":"Answer"}\n',
        encoding="utf-8",
    )
    hash_path.write_text("0" * 64, encoding="ascii")

    with pytest.raises(EvaluationError, match="hash mismatch"):
        load_eval_set(data_path, hash_path)


def test_known_good_stub_scores_full_fixture() -> None:
    tasks, _ = load_eval_set()
    result = run_evaluation(tasks, stub_predict)
    assert result.n_tasks == 6
    assert result.score == 1.0


def test_negative_control_is_strictly_worse_than_known_good_stub() -> None:
    tasks, _ = load_eval_set()
    control, baseline = run_negative_control(tasks)

    assert baseline.score == 1.0
    assert control.score < baseline.score


def test_negative_control_cli_prints_machine_readable_result() -> None:
    completed = subprocess.run(
        [sys.executable, "-m", "eval.runner", "--negative-control"],
        cwd=REPOSITORY_ROOT,
        capture_output=True,
        text=True,
        check=False,
        timeout=15,
    )
    assert completed.returncode == 0, completed.stderr
    output = json.loads(completed.stdout)
    assert output["negative_control_pass"] is True
    assert output["score"] < output["baseline_score"]
    assert output["n_tasks"] == 6


def test_quarantine_rejects_an_eval_question_in_training_data(tmp_path) -> None:
    training = tmp_path / "data" / "training"
    training.mkdir(parents=True)
    (training / "corpus.jsonl").write_text(
        '{"text":"What is 2 + 2?"}\n',
        encoding="utf-8",
    )

    with pytest.raises(QuarantineError, match="leaked"):
        check_training_data(tmp_path, ["What is 2 + 2?"])


def test_quarantine_rejects_uninspectable_training_files(tmp_path) -> None:
    training = tmp_path / "training"
    training.mkdir()
    (training / "archive.bin").write_bytes(b"opaque")

    with pytest.raises(QuarantineError, match="format"):
        check_training_data(tmp_path, ["Question?"])
