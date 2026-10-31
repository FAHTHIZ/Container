# SPDX-License-Identifier: Apache-2.0
"""Create immutable, content-addressed file snapshots with mandatory SHA-256."""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from pathlib import Path
from typing import Any

from container_api.config import settings
from container_api.models import Snapshot


class SnapshotCreationError(RuntimeError):
    """Raised when a snapshot cannot be read, hashed, or stored safely."""


def _digest_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        while chunk := source.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def create_snapshot(
    path: str | Path,
    *,
    snapshot_root: str | Path | None = None,
    metadata: dict[str, Any] | None = None,
) -> Snapshot:
    """Copy a regular file into content-addressed storage and return its DB record.

    The returned SQLAlchemy object is not committed automatically. The caller
    must add it to a database session and commit it with the surrounding job.
    """
    source_argument = Path(path)
    if source_argument.is_symlink():
        raise SnapshotCreationError("Snapshot sources cannot be symbolic links.")

    try:
        source = source_argument.resolve(strict=True)
        if not source.is_file():
            raise SnapshotCreationError("Snapshot source must be an existing regular file.")

        safe_metadata = {} if metadata is None else metadata
        if not isinstance(safe_metadata, dict):
            raise SnapshotCreationError("Snapshot metadata must be a JSON object.")
        # Confirm metadata can be stored as JSON before creating any snapshot file.
        json.dumps(safe_metadata, sort_keys=True)

        target_root_argument = (
            Path(snapshot_root)
            if snapshot_root is not None
            else settings.artifacts_path / "snapshots"
        )
        if target_root_argument.is_symlink():
            raise SnapshotCreationError("Snapshot storage root cannot be a symbolic link.")
        target_root_argument.mkdir(parents=True, exist_ok=True)
        target_root = target_root_argument.resolve(strict=True)
        if not target_root.is_dir():
            raise SnapshotCreationError("Snapshot storage root is not a directory.")

        before = source.stat()
        digest = hashlib.sha256()
        temporary_path: Path | None = None
        try:
            with source.open("rb") as input_file, tempfile.NamedTemporaryFile(
                mode="wb",
                dir=target_root,
                prefix=".snapshot-",
                delete=False,
            ) as output_file:
                temporary_path = Path(output_file.name)
                while chunk := input_file.read(1024 * 1024):
                    digest.update(chunk)
                    output_file.write(chunk)
                output_file.flush()
                os.fsync(output_file.fileno())

            after = source.stat()
            if (
                before.st_size != after.st_size
                or before.st_mtime_ns != after.st_mtime_ns
                or before.st_ino != after.st_ino
            ):
                raise SnapshotCreationError("Snapshot source changed while it was being copied.")

            sha256 = digest.hexdigest()
            if len(sha256) != 64:
                raise SnapshotCreationError("Snapshot hashing did not produce a SHA-256 digest.")

            target = target_root / f"{sha256}.snapshot"
            try:
                # A hard link is atomic and refuses to overwrite existing content.
                os.link(temporary_path, target)
            except FileExistsError as exc:
                if target.is_symlink() or not target.is_file():
                    raise SnapshotCreationError(
                        "Existing snapshot target is not a regular file."
                    ) from exc
                if _digest_file(target) != sha256:
                    raise SnapshotCreationError(
                        "Existing content-addressed snapshot failed verification."
                    ) from exc

            if _digest_file(target) != sha256:
                raise SnapshotCreationError("Stored snapshot failed SHA-256 verification.")
        finally:
            if temporary_path is not None:
                temporary_path.unlink(missing_ok=True)

        stored_path = target.resolve(strict=True)
        if not stored_path.is_relative_to(target_root):
            raise SnapshotCreationError("Stored snapshot escaped its storage root.")
        return Snapshot(
            sha256=sha256,
            path=str(stored_path),
            metadata_json=safe_metadata,
        )
    except SnapshotCreationError:
        raise
    except (OSError, TypeError, ValueError) as exc:
        raise SnapshotCreationError("Snapshot could not be read, hashed, or stored.") from exc
