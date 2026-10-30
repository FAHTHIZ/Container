# SPDX-License-Identifier: Apache-2.0
"""Tests for authenticated host capability inventory."""

from container_api.hardware import collect_capabilities


def test_capability_inventory_is_conservative(monkeypatch):
    monkeypatch.setattr("container_api.hardware._detect_accelerators", lambda: [])
    result = collect_capabilities()

    assert result["scope"] == "API worker host visible to this process"
    assert result["inventory_only"] is True
    assert result["cpu"]["logical_cores"] >= 1
    assert result["cpu"]["effective_cores"] > 0
    assert "container_limit_bytes" in result["memory"]
    assert result["accelerators"] == []
    assert any("not proof" in note for note in result["notes"])


def test_capability_endpoint_requires_authentication(client):
    response = client.get("/api/v1/system/capabilities")
    assert response.status_code == 401


def test_capability_endpoint_returns_inventory(client):
    registered = client.post(
        "/api/v1/auth/register",
        json={
            "email": "hardware@example.com",
            "password": "a-very-long-test-password",
            "display_name": "Hardware Tester",
            "workspace_name": "Hardware Workspace",
        },
    )
    assert registered.status_code == 201
    headers = {"Authorization": f"Bearer {registered.json()['access_token']}"}

    response = client.get("/api/v1/system/capabilities", headers=headers)
    assert response.status_code == 200
    assert response.json()["inventory_only"] is True
    assert "cpu" in response.json()
    assert "memory" in response.json()
    assert "accelerators" in response.json()
