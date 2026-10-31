# SPDX-License-Identifier: Apache-2.0
"""End-to-end tests for project-scoped frozen evaluation jobs."""

import hashlib
import json

from container_api.config import settings
from container_api.routes import artifacts as artifact_routes
from container_api.storage import LocalArtifactStore
from container_api.worker import process_one_job

EVAL_HASH = "389a1294bfa27fad61ce91e2a99c8731682c3c3bd33a7a79623695b29c7ad693"


def register(client, email: str) -> dict:
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "A-Strong-Example-Password-2026",
            "display_name": "Eval Tester",
            "workspace_name": "Evaluation Workspace",
        },
    )
    assert response.status_code == 201, response.text
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def create_project(client, headers: dict, name: str = "Evaluation Project") -> dict:
    workspaces = client.get("/api/v1/workspaces", headers=headers)
    assert workspaces.status_code == 200
    workspace_id = workspaces.json()[0]["id"]
    response = client.post(
        f"/api/v1/workspaces/{workspace_id}/projects",
        headers=headers,
        json={"name": name},
    )
    assert response.status_code == 201, response.text
    return response.json()


def create_model(client, headers: dict, project_id: str) -> dict:
    response = client.post(
        f"/api/v1/projects/{project_id}/models",
        headers=headers,
        json={"name": "Evaluation fixture model", "origin": "imported"},
    )
    assert response.status_code == 201, response.text
    return response.json()


def submit_eval(client, headers: dict, project_id: str, model_id: str, **overrides):
    payload = {
        "kind": "eval_run",
        "model_id": model_id,
        "eval_path": "eval/data/eval.jsonl",
        "eval_hash": EVAL_HASH,
    }
    payload.update(overrides)
    return client.post(
        f"/api/v1/projects/{project_id}/jobs",
        headers=headers,
        json=payload,
    )


def test_eval_run_job_produces_sha256_report_artifact(
    client, test_session_factory, tmp_path, monkeypatch
):
    artifact_root = tmp_path / "evaluation-artifacts"
    monkeypatch.setattr(settings, "eval_predictor", "eval.stub_predictor:predict")
    monkeypatch.setattr(settings, "eval_timeout_seconds", 20)
    monkeypatch.setattr(settings, "artifacts_path", artifact_root)
    monkeypatch.setattr(settings, "max_artifact_bytes", 1024 * 1024)
    monkeypatch.setattr(
        artifact_routes,
        "artifact_store",
        LocalArtifactStore(artifact_root),
    )

    headers = register(client, "eval-owner@example.com")
    project = create_project(client, headers)
    model = create_model(client, headers, project["id"])

    submitted = submit_eval(client, headers, project["id"], model["id"])
    assert submitted.status_code == 201, submitted.text
    job = submitted.json()
    assert job["status"] == "queued"
    assert job["kind"] == "eval_run"

    with test_session_factory() as db:
        assert process_one_job(db) is True

    completed = client.get(f"/api/v1/jobs/{job['id']}", headers=headers)
    assert completed.status_code == 200, completed.text
    result = completed.json()["result"]
    assert completed.json()["status"] == "succeeded"
    assert result["model_id"] == model["id"]
    assert result["eval_hash"] == EVAL_HASH
    assert result["n_tasks"] == 6
    assert result["score"] == 1.0
    assert len(result["artifact_sha256"]) == 64

    artifacts = client.get(
        f"/api/v1/projects/{project['id']}/artifacts",
        headers=headers,
    )
    assert artifacts.status_code == 200
    report = next(item for item in artifacts.json() if item["id"] == result["artifact_id"])
    assert report["sha256"] == result["artifact_sha256"]
    assert report["media_type"] == "application/json"

    downloaded = client.get(
        f"/api/v1/artifacts/{report['id']}/download",
        headers=headers,
    )
    assert downloaded.status_code == 200
    assert hashlib.sha256(downloaded.content).hexdigest() == report["sha256"]
    report_json = json.loads(downloaded.content)
    assert report_json["model_id"] == model["id"]
    assert report_json["eval_hash"] == EVAL_HASH
    assert report_json["score"] == 1.0


def test_eval_job_requires_an_operator_configured_predictor(client, monkeypatch):
    monkeypatch.setattr(settings, "eval_predictor", "")
    headers = register(client, "eval-unconfigured@example.com")
    project = create_project(client, headers)
    model = create_model(client, headers, project["id"])

    response = submit_eval(client, headers, project["id"], model["id"])

    assert response.status_code == 503
    assert "predictor adapter" in response.json()["detail"]


def test_eval_job_rejects_a_model_from_another_project(client, monkeypatch):
    monkeypatch.setattr(settings, "eval_predictor", "eval.stub_predictor:predict")
    headers = register(client, "eval-scope@example.com")
    first_project = create_project(client, headers, "First project")
    second_project = create_project(client, headers, "Second project")
    model = create_model(client, headers, first_project["id"])

    response = submit_eval(client, headers, second_project["id"], model["id"])

    assert response.status_code == 404


def test_eval_job_rejects_invalid_hash_before_queueing(client, monkeypatch):
    monkeypatch.setattr(settings, "eval_predictor", "eval.stub_predictor:predict")
    headers = register(client, "eval-hash@example.com")
    project = create_project(client, headers)
    model = create_model(client, headers, project["id"])

    response = submit_eval(
        client,
        headers,
        project["id"],
        model["id"],
        eval_hash="not-a-sha256",
    )

    assert response.status_code == 422


def test_eval_job_fails_closed_for_path_outside_eval_directory(
    client, test_session_factory, monkeypatch
):
    artifact_root = tmp_path = None
    monkeypatch.setattr(settings, "eval_predictor", "eval.stub_predictor:predict")
    monkeypatch.setattr(settings, "eval_timeout_seconds", 20)
    headers = register(client, "eval-path@example.com")
    project = create_project(client, headers)
    model = create_model(client, headers, project["id"])

    submitted = submit_eval(
        client,
        headers,
        project["id"],
        model["id"],
        eval_path="../README.md",
    )
    assert submitted.status_code == 201, submitted.text
    job_id = submitted.json()["id"]

    with test_session_factory() as db:
        assert process_one_job(db) is True

    failed = client.get(f"/api/v1/jobs/{job_id}", headers=headers)
    assert failed.status_code == 200
    assert failed.json()["status"] == "failed"
    assert "eval directory" in failed.json()["error_message"].lower()
