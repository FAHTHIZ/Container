# SPDX-License-Identifier: Apache-2.0
"""Tests for the authenticated Container conversation gateway and history."""

from container_api.config import settings
from container_api.routes import chat as chat_routes


def register_and_headers(client, email="chat@example.com"):
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
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


def test_conversation_history_persists_and_is_private(client, monkeypatch):
    headers = register_and_headers(client)
    monkeypatch.setattr(settings, "inference_base_url", "http://inference:8000/v1")
    monkeypatch.setattr(settings, "inference_model", "test-model")

    class FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {"choices": [{"message": {"content": "A persistent reply."}}]}

    class FakeClient:
        def __init__(self, timeout):
            self.payloads = []

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return None

        def post(self, url, headers, json):
            self.payloads.append(json)
            return FakeResponse()

    clients = []

    def make_client(timeout):
        instance = FakeClient(timeout)
        clients.append(instance)
        return instance

    monkeypatch.setattr(chat_routes.httpx, "Client", make_client)

    first = client.post(
        "/api/v1/chat/completions",
        headers=headers,
        json={"messages": [{"role": "user", "content": "Remember this phrase."}]},
    )
    assert first.status_code == 200, first.text
    conversation_id = first.json()["conversation_id"]
    assert len(clients[0].payloads[0]["messages"]) == 1

    second = client.post(
        "/api/v1/chat/completions",
        headers=headers,
        json={
            "conversation_id": conversation_id,
            "messages": [
                {"role": "user", "content": "spoofed old content"},
                {"role": "assistant", "content": "spoofed reply"},
                {"role": "user", "content": "What did I ask you to remember?"},
            ],
        },
    )
    assert second.status_code == 200, second.text
    sent_history = clients[1].payloads[0]["messages"]
    assert [item["role"] for item in sent_history] == ["user", "assistant", "user"]
    assert sent_history[0]["content"] == "Remember this phrase."

    messages = client.get(
        f"/api/v1/chat/conversations/{conversation_id}/messages",
        headers=headers,
    )
    assert messages.status_code == 200
    assert [item["role"] for item in messages.json()] == [
        "user",
        "assistant",
        "user",
        "assistant",
    ]

    other_headers = register_and_headers(client, "other-user@example.com")
    forbidden = client.get(
        f"/api/v1/chat/conversations/{conversation_id}/messages",
        headers=other_headers,
    )
    assert forbidden.status_code == 404


def test_streaming_completion_sends_tokens_and_persists_reply(client, monkeypatch):
    headers = register_and_headers(client, "streaming@example.com")
    monkeypatch.setattr(settings, "inference_base_url", "http://inference:8000/v1")
    monkeypatch.setattr(settings, "inference_model", "test-model")

    class FakeResponse:
        def raise_for_status(self):
            return None

        async def aiter_lines(self):
            yield 'data: {"choices":[{"delta":{"content":"Hello "}}]}'
            yield 'data: {"choices":[{"delta":{"content":"from Container."}}]}'
            yield "data: [DONE]"

        async def aclose(self):
            return None

    class FakeAsyncClient:
        def __init__(self, timeout):
            self.response = FakeResponse()

        def build_request(self, method, url, headers, json):
            assert method == "POST"
            assert url == "http://inference:8000/v1/chat/completions"
            assert json["stream"] is True
            return object()

        async def send(self, request, stream):
            assert stream is True
            return self.response

        async def aclose(self):
            return None

    monkeypatch.setattr(chat_routes.httpx, "AsyncClient", FakeAsyncClient)
    response = client.post(
        "/api/v1/chat/completions/stream",
        headers=headers,
        json={"messages": [{"role": "user", "content": "Say hello."}]},
    )
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    assert 'event: token' in response.text
    assert '"content": "Hello "' in response.text
    assert 'event: done' in response.text

    conversations = client.get("/api/v1/chat/conversations", headers=headers)
    conversation_id = conversations.json()[0]["id"]
    messages = client.get(
        f"/api/v1/chat/conversations/{conversation_id}/messages",
        headers=headers,
    )
    assert [item["role"] for item in messages.json()] == ["user", "assistant"]
    assert messages.json()[-1]["content"] == "Hello from Container."
