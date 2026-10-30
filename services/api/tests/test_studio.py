# SPDX-License-Identifier: Apache-2.0
"""Smoke tests for the first-party browser Studio and static assets."""


def test_studio_page_is_served(client) -> None:
    response = client.get("/studio")
    assert response.status_code == 200
    assert "Container Studio" in response.text
    assert 'id="auth-form"' in response.text
    assert "/studio-assets/app.js" in response.text


def test_studio_assets_are_served(client) -> None:
    javascript = client.get("/studio-assets/app.js")
    stylesheet = client.get("/studio-assets/app.css")

    assert javascript.status_code == 200
    assert javascript.headers["content-type"].startswith("text/javascript")
    assert "DOMContentLoaded" in javascript.text
    assert stylesheet.status_code == 200
    assert stylesheet.headers["content-type"].startswith("text/css")
