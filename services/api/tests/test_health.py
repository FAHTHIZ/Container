# SPDX-License-Identifier: Apache-2.0
"""Tests for API metadata and the packaged first-party Studio."""

from fastapi.testclient import TestClient

from container_api.main import app

client = TestClient(app)


def test_root_returns_service_metadata() -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["name"] == "Container API"
    assert response.json()["studio"] == "/studio"


def test_liveness_probe() -> None:
    response = client.get("/health/live")
    assert response.status_code == 200
    assert response.json() == {"status": "alive"}


def test_readiness_probe() -> None:
    response = client.get("/health/ready")
    assert response.status_code == 200
    assert response.json()["status"] == "ready"


def test_studio_and_assets_are_served() -> None:
    page = client.get("/studio")
    script = client.get("/studio-assets/app.js")
    stylesheet = client.get("/studio-assets/app.css")

    assert page.status_code == 200
    assert "Container Studio" in page.text
    assert 'id="artifact-form"' in page.text
    assert 'id="model-form"' in page.text
    assert script.status_code == 200
    assert "text/event-stream" in script.text
    assert "uploadArtifact" in script.text
    assert "createModelVersion" in script.text
    assert stylesheet.status_code == 200
    assert ".artifact-item" in stylesheet.text
    assert ".model-item" in stylesheet.text
