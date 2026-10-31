# SPDX-License-Identifier: Apache-2.0
"""Tests for external trainer orchestration and hash-required checkpoint records."""

import hashlib

from container_api.config import settings
from container_api.routes import artifacts as artifact_routes
from container_api.storage import LocalArtifactStore
from container_api.worker import process_one_job

EVAL_HASH = "389a1294bfa27fad61ce91e2a99c8731682c3c3bd33a7a79623695b29c7ad693"


def register(client, email: str) -> dict[str, str]:
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "A-Strong-Example-Password-2026",
            "display_name": "Training Test",
            "workspace_name": "Training Workspace",
        },
    )
    assert response.status_code == 201, response.text
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def create_project(client, headers: dict[str, str]) -> dict:
    workspaces = client.get("/api/v1/workspaces", headers=headers)
    assert workspaces.status_code == 200
    workspace_id = workspaces.json()[0]["id"]
    response = client.post(
        f"/api/v1/workspaces/{workspace_id}/projects",
        headers=headers,
        json={"name": "Training Project"},
    )
    assert response.status_code == 201, response.text
    return response.json()


def create_model(client, headers: dict[str, str], project_id: str) -> dict:
    response = client.post(
        f"/api/v1/projects/{project_id}/models",
        headers=headers,
        json={"name": "External Trainer Test Model", "origin": "custom"},
    )
    assert response.status_code == 201, response.text
    return response.json()


def upload_dataset(client, headers: dict[str, str], project_id: str, data: bytes) -> dict:
    response = client.post(
        f"/api/v1/projects/{project_id}/artifacts",
        headers=headers,
        files={"file": ("training.txt", data, "text/plain")},
    )
    assert response.status_code == 201, response.text
    return response.json()


def submit_train(
    client,
    headers: dict[str, str],
    project_id: str,
    model_id: str,
    dataset_id: str,
) -> dict:
    return client.post(
        f"/api/v1/projects/{project_id}/jobs",
        headers=headers,
        json={
            "kind": "train_run",
            "model_id": model_id,
            "dataset_artifact_id": dataset_id,
            "steps": 4,
            "loss_every": 2,
            "checkpoint_every": 2,
            "eval_path": "eval/data/eval.jsonl",
            "eval_hash": EVAL_HASH,
        },
    )


def configure_test_adapters(monkeypatch, artifact_root) -> None:
    monkeypatch.setattr(settings, "train_runner", "training_fixtures.adapter:run_training")
    monkeypatch.setattr(settings, "eval_predictor", "eval.checkpoint_stub_predictor:predict")
    monkeypatch.setattr(settings, "train_timeout_seconds", 20)
    monkeypatch.setattr(settings, "eval_timeout_seconds", 20)
    monkeypatch.setattr(settings, "artifacts_path", artifact_root)
    monkeypatch.setattr(settings, "max_artifact_bytes", 1024 * 1024)
    monkeypatch.setattr(
        artifact_routes,
        "artifact_store",
        LocalArtifactStore(artifact_root),
    )


def test_train_run_stores_hashed_checkpoints_and_evaluates_the_final_one(
    client, test_session_factory, tmp_path, monkeypatch
):
    artifact_root = tmp_path / "training-artifacts"
    configure_test_adapters(monkeypatch, artifact_root)
    headers = register(client, "train-owner@example.com")
    project = create_project(client, headers)
    model = create_model(client, headers, project["id"])
    dataset = upload_dataset(
        client,
        headers,
        project["id"],
        b"Only ordinary training examples. No frozen evaluation questions.\n",
    )

    submitted = submit_train(
        client, headers, project["id"], model["id"], dataset["id"]
    )
    assert submitted.status_code == 201, submitted.text
    job_id = submitted.json()["id"]
    assert submitted.json()["kind"] == "train_run"

    with test_session_factory() as db:
        assert process_one_job(db) is True

    completed = client.get(f"/api/v1/jobs/{job_id}", headers=headers)
    assert completed.status_code == 200, completed.text
    job = completed.json()
    assert job["status"] == "succeeded", job["error_message"]

    result = job["result"]
    assert result["steps_completed"] == 4
    assert result["loss_records"] == [
        {"step": 2, "loss": 0.33333333},
        {"step": 4, "loss": 0.2},
    ]
    assert len(result["checkpoints"]) == 2
    assert result["checkpoint_hash"] == result["checkpoints"][-1]["checkpoint_hash"]
    assert result["eval_score"] == 1.0
    assert result["eval_hash"] == EVAL_HASH
    assert result["n_tasks"] == 6

    for checkpoint in result["checkpoints"]:
        artifact = client.get(
            f"/api/v1/artifacts/{checkpoint['artifact_id']}/download",
            headers=headers,
        )
        assert artifact.status_code == 200
        assert hashlib.sha256(artifact.content).hexdigest() == checkpoint["checkpoint_hash"]

    versions = client.get(f"/api/v1/models/{model['id']}/versions", headers=headers)
    assert versions.status_code == 200
    version = next(
        item for item in versions.json()
        if item["id"] == result["model_version_id"]
    )
    assert version["details"]["checkpoint_hash"] == result["checkpoint_hash"]
    assert version["details"]["eval_score"] == result["eval_score"]
    assert version["artifact_id"] == result["checkpoints"][-1]["artifact_id"]

    report = client.get(
        f"/api/v1/artifacts/{result['evaluation_artifact_id']}/download",
        headers=headers,
    )
    assert report.status_code == 200
    assert hashlib.sha256(report.content).hexdigest() == result["evaluation_artifact_sha256"]


def test_train_run_requires_both_trusted_adapters(client, monkeypatch):
    monkeypatch.setattr(settings, "train_runner", "")
    monkeypatch.setattr(settings, "eval_predictor", "")
    headers = register(client, "train-unconfigured@example.com")
    project = create_project(client, headers)
    model = create_model(client, headers, project["id"])
    dataset = upload_dataset(client, headers, project["id"], b"safe dataset\n")

    response = submit_train(client, headers, project["id"], model["id"], dataset["id"])

    assert response.status_code == 503


def test_train_run_rejects_eval_question_leakage_before_adapter_starts(
    client, test_session_factory, tmp_path, monkeypatch
):
    artifact_root = tmp_path / "leak-test-artifacts"
    configure_test_adapters(monkeypatch, artifact_root)
    headers = register(client, "train-leak@example.com")
    project = create_project(client, headers)
    model = create_model(client, headers, project["id"])
    dataset = upload_dataset(
        client,
        headers,
        project["id"],
        b"Training prompt: What is 2 + 2?\n",
    )
    submitted = submit_train(
        client, headers, project["id"], model["id"], dataset["id"]
    )
    assert submitted.status_code == 201, submitted.text

    with test_session_factory() as db:
        assert process_one_job(db) is True

    failed = client.get(
        f"/api/v1/jobs/{submitted.json()['id']}",
        headers=headers,
    )
    assert failed.status_code == 200
    assert failed.json()["status"] == "failed"
    assert "frozen evaluation question" in failed.json()["error_message"]


def test_train_run_fails_if_any_loss_interval_is_missing(
    client, test_session_factory, tmp_path, monkeypatch
):
    artifact_root = tmp_path / "missing-loss-artifacts"
    configure_test_adapters(monkeypatch, artifact_root)
    monkeypatch.setattr(
        settings,
        "train_runner",
        "training_fixtures.adapter:omit_one_loss_record",
    )
    headers = register(client, "train-loss@example.com")
    project = create_project(client, headers)
    model = create_model(client, headers, project["id"])
    dataset = upload_dataset(client, headers, project["id"], b"safe dataset\n")
    submitted = submit_train(
        client, headers, project["id"], model["id"], dataset["id"]
    )
    assert submitted.status_code == 201, submitted.text

    with test_session_factory() as db:
        assert process_one_job(db) is True

    failed = client.get(
        f"/api/v1/jobs/{submitted.json()['id']}",
        headers=headers,
    )
    assert failed.status_code == 200
    assert failed.json()["status"] == "failed"
    assert "loss at every requested interval" in failed.json()["error_message"]
