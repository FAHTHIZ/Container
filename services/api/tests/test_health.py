# SPDX-License-Identifier: Apache-2.0
from fastapi.testclient import TestClient

from container_api.main import app

client = TestClient(app)


def test_root_returns_service_metadata() -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["name"] == "Container API"
    assert response.json()["status"] == "foundation"


def test_liveness_probe() -> None:
    response = client.get("/health/live")
    assert response.status_code == 200
    assert response.json() == {"status": "alive"}


def test_readiness_probe() -> None:
    response = client.get("/health/ready")
    assert response.status_code == 200
    assert response.json()["status"] == "ready"
