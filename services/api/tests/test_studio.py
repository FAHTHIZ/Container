# SPDX-License-Identifier: Apache-2.0
"""Smoke tests for the first-party browser Studio and static assets."""


def test_studio_page_is_served(client) -> None:
    response = client.get("/studio")
    assert response.status_code == 200
    assert "Container Studio" in response.text
    assert 'id="auth-form"' in response.text
    assert 'id="chat-panel"' in response.text
    assert "/studio-assets/app.js" in response.text


def test_installable_app_shell_is_served(client) -> None:
    manifest = client.get("/manifest.webmanifest")
    worker = client.get("/sw.js")
    assert manifest.status_code == 200
    assert manifest.json()["name"] == "Container"
    assert worker.status_code == 200
    assert "Cache-Control" in worker.headers


def test_studio_assets_are_served(client) -> None:
    javascript = client.get("/studio-assets/app.js")
    stylesheet = client.get("/studio-assets/app.css")
    chat = client.get("/studio-assets/chat.js")
    pwa = client.get("/studio-assets/pwa.js")

    assert javascript.status_code == 200
    assert javascript.headers["content-type"].startswith("text/javascript")
    assert "DOMContentLoaded" in javascript.text
    assert chat.status_code == 200
    assert "chat/completions" in chat.text
    assert pwa.status_code == 200
    assert "serviceWorker.register" in pwa.text
    assert stylesheet.status_code == 200
    assert stylesheet.headers["content-type"].startswith("text/css")


def test_service_worker_does_not_cache_authenticated_api(client) -> None:
    worker = client.get("/sw.js")
    assert worker.status_code == 200
    assert 'url.pathname.startsWith("/api/")' in worker.text
