# SPDX-License-Identifier: Apache-2.0
"""Tests for safe external model source inspection."""

from types import SimpleNamespace

from container_api.routes import model_sources


def auth_headers(client):
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "model-source@example.com",
            "password": "a-very-long-test-password",
            "display_name": "Model Tester",
            "workspace_name": "Model Workspace",
        },
    )
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def test_model_inspection_rejects_untrusted_hosts(client):
    headers = auth_headers(client)
    response = client.post(
        "/api/v1/model-sources/inspect",
        headers=headers,
        json={"url": "https://example.com/owner/model"},
    )
    assert response.status_code == 422


def test_model_inspection_returns_metadata_without_downloading_files(client, monkeypatch):
    headers = auth_headers(client)

    class FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {
                "id": "acme/demo-model",
                "pipeline_tag": "text-generation",
                "library_name": "transformers",
                "cardData": {"license": "apache-2.0"},
                "downloads": 1200,
                "likes": 20,
                "gated": False,
                "private": False,
                "siblings": [{"rfilename": "config.json"}, {"rfilename": "model.safetensors"}],
            }

    def fake_get(url, headers, timeout):
        assert url == "https://huggingface.co/api/models/acme/demo-model"
        assert timeout == 15.0
        return FakeResponse()

    monkeypatch.setattr(model_sources.httpx, "get", fake_get)
    response = client.post(
        "/api/v1/model-sources/inspect",
        headers=headers,
        json={"url": "https://huggingface.co/acme/demo-model"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["model_id"] == "acme/demo-model"
    assert data["license"] == "apache-2.0"
    assert data["file_count"] == 2
    assert data["inspection_only"] is True
