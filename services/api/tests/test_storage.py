# SPDX-License-Identifier: Apache-2.0
"""Tests for immutable, bounded local artifact storage."""

from io import BytesIO

import pytest

from container_api.storage import LocalArtifactStore


def test_put_returns_digest_and_gets_exact_bytes(tmp_path) -> None:
    store = LocalArtifactStore(tmp_path / "artifacts")
    payload = b"Container artifact test\x00payload"

    stored = store.put("workspace/project/blob.bin", BytesIO(payload), max_bytes=1024)

    assert stored.size_bytes == len(payload)
    assert len(stored.sha256) == 64
    assert store.get_path(stored.key).read_bytes() == payload
    assert store.exists(stored.key)


def test_artifact_keys_cannot_escape_storage_root(tmp_path) -> None:
    store = LocalArtifactStore(tmp_path / "artifacts")

    for key in ("../outside.txt", "/absolute.txt", "folder/../../outside.txt", "C:/outside.txt"):
        with pytest.raises(ValueError):
            store.put(key, BytesIO(b"no"), max_bytes=100)


def test_artifact_upload_is_bounded_and_cleans_temporary_file(tmp_path) -> None:
    store = LocalArtifactStore(tmp_path / "artifacts")

    with pytest.raises(ValueError, match="size limit"):
        store.put("large.bin", BytesIO(b"x" * 20), max_bytes=10)

    assert not store.exists("large.bin")
    assert list((tmp_path / "artifacts").iterdir()) == []


def test_artifact_keys_are_immutable(tmp_path) -> None:
    store = LocalArtifactStore(tmp_path / "artifacts")
    store.put("immutable.bin", BytesIO(b"first"), max_bytes=100)

    with pytest.raises(FileExistsError):
        store.put("immutable.bin", BytesIO(b"second"), max_bytes=100)

    assert store.get_path("immutable.bin").read_bytes() == b"first"
