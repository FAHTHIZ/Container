# SPDX-License-Identifier: Apache-2.0
"""Smoke tests for the first-party browser Studio and static assets."""


def test_studio_page_is_served(client) -> None:
    response = client.get("/studio")
    assert response.status_code == 200
    assert "Container Studio" in response.text
    assert 'id="auth-form"' in response.text
    assert "/studio-assets/app.js" in response.text


def test_installable_app_shell_is_served(client) -> None:\n    manifest = client.get("/manifest.webmanifest")\n    worker = client.get("/sw.js")\n    assert manifest.status_code == 200\n    assert manifest.json()["name"] == "Container"\n    assert worker.status_code == 200\n    assert "Cache-Control" in worker.headers\n\n\ndef test_studio_assets_are_served(client) -> None:
    javascript = client.get("/studio-assets/app.js")
    stylesheet = client.get("/studio-assets/app.css")

    assert javascript.status_code == 200
    assert javascript.headers["content-type"].startswith("text/javascript")
    assert "DOMContentLoaded" in javascript.text\n    pwa = client.get("/studio-assets/pwa.js")\n    assert pwa.status_code == 200\n    assert "serviceWorker.register" in pwa.text
    assert stylesheet.status_code == 200
    assert stylesheet.headers["content-type"].startswith("text/css")
