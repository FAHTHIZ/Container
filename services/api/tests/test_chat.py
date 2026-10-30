# SPDX-License-Identifier: Apache-2.0
"""Tests for the authenticated Container conversation gateway."""

from container_api.config import settings


def register_and_headers(client):
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "chat@example.com",
            "password": "a-very-long-test-password",
            "display_name": "Chat Tester",
            "workspace_name": "Chat Workspace",
        },
    )
    assert response.status_code == 201
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def test_chat_status_requires_authentication(client):
    response = client.get("/api/v1/chat/status")
    assert response.status_code == 401


def test_chat_reports_unconfigured_inference_without_exposing_secrets(client, monkeypatch):
    headers = register_and_headers(client)
    monkeypatch.setattr(settings, "inference_base_url", "")
    monkeypatch.setattr(settings, "inference_model", "")
    response = client.get("/api/v1/chat/status", headers=headers)
    assert response.status_code == 200
    assert response.json()["configured"] is False
    assert "api_key" not in response.text.lower()


def test_chat_completion_requires_a_configured_inference_service(client, monkeypatch):
    headers = register_and_headers(client)
    monkeypatch.setattr(settings, "inference_base_url", "")
    monkeypatch.setattr(settings, "inference_model", "")
    response = client.post(
        "/api/v1/chat/completions",
        headers=headers,
        json={"messages": [{"role": "user", "content": "Hello"}]},
    )
    assert response.status_code == 503
    assert "not connected" in response.json()["detail"].lower()


def test_chat_requires_user_as_last_message(client, monkeypatch):
    headers = register_and_headers(client)
    monkeypatch.setattr(settings, "inference_base_url", "http://inference:8000/v1")
    monkeypatch.setattr(settings, "inference_model", "test-model")
    response = client.post(
        "/api/v1/chat/completions",
        headers=headers,
        json={"messages": [{"role": "assistant", "content": "Only assistant"}]},
    )
    assert response.status_code == 422
