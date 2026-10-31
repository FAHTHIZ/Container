# SPDX-License-Identifier: Apache-2.0
"""Tests for hash-required immutable snapshots."""

import hashlib
from pathlib import Path

import pytest

from container_api.models import Snapshot
from container_api.snapshots import SnapshotCreationError, create_snapshot


def test_snapshot_is_copied_and_sha256_is_stored(tmp_path) -> None:
    source = tmp_path / "weights.bin"
    payload = b"snapshot bytes must be hashed"
    source.write_bytes(payload)

    snapshot = create_snapshot(source, snapshot_root=tmp_path / "snapshots")

    assert isinstance(snapshot, Snapshot)
    assert snapshot.sha256 == hashlib.sha256(payload).hexdigest()
    stored_path = tmp_path / "snapshots" / f"{snapshot.sha256}.snapshot"
    assert snapshot.path == str(stored_path.resolve())
    assert stored_path.read_bytes() == payload
    assert len(snapshot.sha256) == 64


def test_snapshot_refuses_a_missing_source(tmp_path) -> None:
    with pytest.raises(SnapshotCreationError):
        create_snapshot(tmp_path / "missing.bin", snapshot_root=tmp_path / "snapshots")

    assert not (tmp_path / "snapshots").exists()


def test_snapshot_is_immutable_when_source_changes_after_capture(tmp_path) -> None:
    source = tmp_path / "weights.bin"
    source.write_bytes(b"first version")
    snapshot = create_snapshot(source, snapshot_root=tmp_path / "snapshots")

    source.write_bytes(b"second version")

    assert snapshot.sha256 == hashlib.sha256(b"first version").hexdigest()
    assert Path(snapshot.path).read_bytes() == b"first version"


def test_snapshot_refuses_symbolic_link_sources(tmp_path) -> None:
    source = tmp_path / "real.bin"
    source.write_bytes(b"content")
    link = tmp_path / "link.bin"
    link.symlink_to(source)

    with pytest.raises(SnapshotCreationError):
        create_snapshot(link, snapshot_root=tmp_path / "snapshots")


def test_snapshot_metadata_must_be_json_serializable(tmp_path) -> None:
    source = tmp_path / "weights.bin"
    source.write_bytes(b"content")

    with pytest.raises(SnapshotCreationError):
        create_snapshot(
            source,
            snapshot_root=tmp_path / "snapshots",
            metadata={"not-json": object()},
        )


def test_snapshot_record_persists_with_digest(test_session_factory, tmp_path) -> None:
    source = tmp_path / "persist.bin"
    source.write_bytes(b"persisted snapshot")
    snapshot = create_snapshot(source, snapshot_root=tmp_path / "snapshots")

    with test_session_factory() as db:
        db.add(snapshot)
        db.commit()
        db.refresh(snapshot)
        stored = db.get(Snapshot, snapshot.id)
        assert stored is not None
        assert stored.sha256 == snapshot.sha256
        assert stored.path == snapshot.path
