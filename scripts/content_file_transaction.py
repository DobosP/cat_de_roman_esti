"""Atomic file writes and verified rollback for offline content mutations."""

from __future__ import annotations

import os
import tempfile
from collections.abc import Iterable, Iterator
from contextlib import contextmanager
from pathlib import Path


class FileTransactionError(RuntimeError):
    """A content-file transaction could not start or roll back completely."""


def atomic_write(path: Path, blob: bytes) -> None:
    """Replace one file without exposing a partially written document."""
    temp_name: str | None = None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as handle:
            temp_name = handle.name
            handle.write(blob)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_name, path)
        temp_name = None
    finally:
        if temp_name is not None:
            try:
                os.unlink(temp_name)
            except FileNotFoundError:
                pass


def snapshot_files(paths: Iterable[Path]) -> dict[Path, bytes]:
    """Read every transaction member before any mutation begins."""
    snapshots: dict[Path, bytes] = {}
    for path in dict.fromkeys(paths):
        try:
            snapshots[path] = path.read_bytes()
        except OSError as exc:
            raise FileTransactionError(f"cannot snapshot {path}: {exc}") from exc
    return snapshots


def restore_files(snapshots: dict[Path, bytes]) -> None:
    """Restore changed members, then byte-verify the complete snapshot."""
    errors: list[str] = []
    for path, blob in snapshots.items():
        try:
            current = path.read_bytes()
        except OSError:
            current = None
        if current == blob:
            continue
        try:
            atomic_write(path, blob)
        except OSError as exc:
            errors.append(f"{path}: {exc}")

    mismatches: list[str] = []
    for path, blob in snapshots.items():
        try:
            if path.read_bytes() != blob:
                mismatches.append(str(path))
        except OSError as exc:
            errors.append(f"{path}: cannot verify restored bytes: {exc}")
    if errors or mismatches:
        detail = "; ".join(
            [*errors, *(f"restore mismatch: {path}" for path in mismatches)]
        )
        raise FileTransactionError(f"transaction rollback was incomplete: {detail}")


@contextmanager
def file_transaction(paths: Iterable[Path]) -> Iterator[dict[Path, bytes]]:
    """Restore every member exactly when any mutation or validation step fails."""
    snapshots = snapshot_files(paths)
    try:
        yield snapshots
    except BaseException as original:
        try:
            restore_files(snapshots)
        except BaseException as rollback:
            raise FileTransactionError(
                f"{original}; additionally, rollback failed: {rollback}"
            ) from original
        raise
