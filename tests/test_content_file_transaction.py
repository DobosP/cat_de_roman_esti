"""Fault-injection tests for offline content-file transactions."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT / "scripts"))

import content_file_transaction as transaction  # noqa: E402


@pytest.mark.parametrize("failed_write", [1, 2])
def test_forward_write_failure_restores_every_snapshot(
    tmp_path,
    monkeypatch,
    failed_write,
):
    paths = (tmp_path / "one.json", tmp_path / "two.json")
    originals = {path: f"original-{index}".encode() for index, path in enumerate(paths)}
    for path, blob in originals.items():
        path.write_bytes(blob)

    real_atomic_write = transaction.atomic_write
    calls = 0

    def fail_selected_write(path, blob):
        nonlocal calls
        calls += 1
        if calls == failed_write:
            raise OSError(f"injected forward write {calls}")
        real_atomic_write(path, blob)

    monkeypatch.setattr(transaction, "atomic_write", fail_selected_write)
    with pytest.raises(OSError, match="injected forward write"):
        with transaction.file_transaction(paths):
            transaction.atomic_write(paths[0], b"changed-one")
            transaction.atomic_write(paths[1], b"changed-two")

    assert {path: path.read_bytes() for path in paths} == originals


def test_exception_after_all_writes_restores_four_file_transaction(tmp_path):
    paths = tuple(tmp_path / f"member-{index}.json" for index in range(4))
    originals = {path: f"original-{index}".encode() for index, path in enumerate(paths)}
    for path, blob in originals.items():
        path.write_bytes(blob)

    with pytest.raises(RuntimeError, match="injected validator failure"):
        with transaction.file_transaction(paths):
            for index, path in enumerate(paths):
                transaction.atomic_write(path, f"changed-{index}".encode())
            raise RuntimeError("injected validator failure")

    assert {path: path.read_bytes() for path in paths} == originals


def test_restore_failure_is_reported_instead_of_claiming_success(tmp_path, monkeypatch):
    paths = (tmp_path / "one.json", tmp_path / "two.json")
    for index, path in enumerate(paths):
        path.write_bytes(f"original-{index}".encode())

    real_atomic_write = transaction.atomic_write
    calls = 0

    def fail_forward_and_restore(path, blob):
        nonlocal calls
        calls += 1
        if calls in {2, 3}:
            raise OSError(f"injected write {calls}")
        real_atomic_write(path, blob)

    monkeypatch.setattr(transaction, "atomic_write", fail_forward_and_restore)
    with pytest.raises(
        transaction.FileTransactionError,
        match="additionally, rollback failed.*rollback was incomplete",
    ):
        with transaction.file_transaction(paths):
            transaction.atomic_write(paths[0], b"changed-one")
            transaction.atomic_write(paths[1], b"changed-two")
