# SPDX-License-Identifier: Apache-2.0
"""End-to-end tests for auth, workspace isolation, jobs, and artifacts."""

import hashlib

from container_api.routes import artifacts as artifact_routes
from container_api.routes import jobs as jobs_routes
from container_api.storage import LocalArtifactStore
from container_api.worker import process_one_job


def register(client, email: str) -> tuple[dict, dict]:
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "A-Strong-Example-Password-2026",
            "display_name": "Test User",
            "workspace_name": "Test Workspace",
        },
    )
    assert response.status_code == 201, response.text
    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    assert client.get("/api/v1/auth/me", headers=headers).status_code == 200
    workspaces = client.get("/api/v1/workspaces", headers=headers)
    assert workspaces.status_code == 200
    return headers, workspaces.json()[0]


def create_project(client, headers: dict, workspace_id: str) -> dict:
    response = client.post(
        f"/api/v1/workspaces/{workspace_id}/projects",
        headers=headers,
        json={"name": "First Project", "description": "Control-plane test"},
    )
    assert response.status_code == 201, response.text
    return response.json()


def test_register_project_and_execute_job(client, test_session_factory, monkeypatch) -> None:
    headers, workspace = register(client, "owner@example.com")
    project = create_project(client, headers, workspace["id"])
    job_response = client.post(
        f"/api/v1/projects/{project['id']}/jobs",
        headers=headers,
        json={"kind": "demo.echo", "message": "Hello from Container"},
    )
    assert job_response.status_code == 201, job_response.text
    job = job_response.json()
    assert job["status"] == "queued"

    with test_session_factory() as db:
        assert process_one_job(db) is True

    completed = client.get(f"/api/v1/jobs/{job['id']}", headers=headers)
    assert completed.status_code == 200
    assert completed.json()["status"] == "succeeded"
    assert completed.json()["progress"] == 100
    assert completed.json()["result"]["message"] == "Hello from Container"

    events = client.get(f"/api/v1/jobs/{job['id']}/events", headers=headers)
    assert events.status_code == 200
    types = [event["event_type"] for event in events.json()]
    assert "job.queued" in types
    assert "job.started" in types
    assert "job.succeeded" in types

    monkeypatch.setattr(jobs_routes, "SessionLocal", test_session_factory)
    stream = client.get(f"/api/v1/jobs/{job['id']}/events/stream", headers=headers)
    assert stream.status_code == 200
    assert stream.headers["content-type"].startswith("text/event-stream")
    assert "job.queued" in stream.text
    assert "job.succeeded" in stream.text


def test_workspace_data_is_not_visible_to_another_user(client) -> None:
    owner_headers, workspace = register(client, "first@example.com")
    other_headers, _ = register(client, "second@example.com")
    created = client.post(
        f"/api/v1/workspaces/{workspace['id']}/projects",
        headers=owner_headers,
        json={"name": "Private Project"},
    )
    assert created.status_code == 201
    forbidden = client.get(
        f"/api/v1/workspaces/{workspace['id']}/projects",
        headers=other_headers,
    )
    assert forbidden.status_code == 404


def test_queued_job_can_be_cancelled(client) -> None:
    headers, workspace = register(client, "cancel@example.com")
    project = create_project(client, headers, workspace["id"])
    job = client.post(
        f"/api/v1/projects/{project['id']}/jobs",
        headers=headers,
        json={"kind": "demo.echo", "message": "Do not run"},
    ).json()
    response = client.post(f"/api/v1/jobs/{job['id']}/cancel", headers=headers)
    assert response.status_code == 200
    assert response.json()["status"] == "cancelled"


def test_api_requires_authentication(client) -> None:
    response = client.get("/api/v1/workspaces")
    assert response.status_code == 401


def test_login_rejects_wrong_password(client) -> None:
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "login@example.com",
            "password": "A-Strong-Example-Password-2026",
            "display_name": "Test User",
            "workspace_name": "Workspace",
        },
    )
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "login@example.com", "password": "wrong-password"},
    )
    assert response.status_code == 401


def test_upload_and_download_project_artifact(client, test_session_factory, tmp_path, monkeypatch):
    monkeypatch.setattr(
        artifact_routes,
        "artifact_store",
        LocalArtifactStore(tmp_path / "artifact-test"),
    )
    headers, workspace = register(client, "artifact-owner@example.com")
    project = create_project(client, headers, workspace["id"])
    payload = b"Container artifact payload"

    uploaded = client.post(
        f"/api/v1/projects/{project['id']}/artifacts",
        headers=headers,
        files={"file": ("../notes.txt", payload, "text/plain")},
    )
    assert uploaded.status_code == 201, uploaded.text
    artifact = uploaded.json()
    assert artifact["filename"] == "notes.txt"
    assert artifact["size_bytes"] == len(payload)
    assert artifact["sha256"] == hashlib.sha256(payload).hexdigest()

    with test_session_factory() as db:
        from container_api.models import Artifact
        stored = db.get(Artifact, artifact["id"])
        assert stored is not None

    listed = client.get(
        f"/api/v1/projects/{project['id']}/artifacts",
        headers=headers,
    )
    assert listed.status_code == 200
    assert listed.json()[0]["id"] == artifact["id"]

    downloaded = client.get(
        f"/api/v1/artifacts/{artifact['id']}/download",
        headers=headers,
    )
    assert downloaded.status_code == 200
    assert downloaded.content == payload
    assert "attachment" in downloaded.headers["content-disposition"]
    assert downloaded.headers["x-content-type-options"] == "nosniff"


def test_artifact_access_is_workspace_scoped(client, tmp_path, monkeypatch):
    monkeypatch.setattr(
        artifact_routes,
        "artifact_store",
        LocalArtifactStore(tmp_path / "artifact-isolation"),
    )
    owner_headers, workspace = register(client, "artifact-one@example.com")
    project = create_project(client, owner_headers, workspace["id"])
    uploaded = client.post(
        f"/api/v1/projects/{project['id']}/artifacts",
        headers=owner_headers,
        files={"file": ("private.bin", b"private payload", "application/octet-stream")},
    )
    assert uploaded.status_code == 201
    artifact_id = uploaded.json()["id"]

    other_headers, _ = register(client, "artifact-two@example.com")
    response = client.get(
        f"/api/v1/artifacts/{artifact_id}/download",
        headers=other_headers,
    )
    assert response.status_code == 404


def test_oversized_artifact_is_rejected(client, tmp_path, monkeypatch):
    monkeypatch.setattr(
        artifact_routes,
        "artifact_store",
        LocalArtifactStore(tmp_path / "artifact-limit"),
    )
    monkeypatch.setattr(settings, "max_artifact_bytes", 3)
    headers, workspace = register(client, "artifact-large@example.com")
    project = create_project(client, headers, workspace["id"])
    response = client.post(
        f"/api/v1/projects/{project['id']}/artifacts",
        headers=headers,
        files={"file": ("big.bin", b"four", "application/octet-stream")},
    )
    assert response.status_code == 413
