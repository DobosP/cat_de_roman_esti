"""Eviction tests for the shared word-game :class:`SessionStore`.

The store must stay bounded so a long-lived server (or a bot spamming ``POST /games``)
cannot leak in-progress sessions without limit. Two mechanisms enforce that — a sliding
TTL and an LRU size cap — and both are exercised here with an injected fake clock so
expiry is deterministic and the tests never sleep.
"""

from __future__ import annotations

import threading

import pytest

from cat_de_roman_esti.wordgames.service import (
    DEFAULT_MAX_SESSIONS,
    DEFAULT_SESSION_TTL_SECONDS,
    SessionCapacityError,
    SessionStore,
    _positive_env_float,
    _positive_env_int,
)


class FakeClock:
    """A manually advanced monotonic clock; call instance to read, ``.advance`` to move."""

    def __init__(self, now: float = 1000.0) -> None:
        self.now = now

    def __call__(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += seconds


def test_create_get_delete_roundtrip():
    store: SessionStore[str] = SessionStore()
    sid = store.create("alpha")
    assert store.get(sid) == "alpha"
    assert len(store) == 1
    assert store.delete(sid) is True
    assert store.get(sid) is None
    assert store.delete(sid) is False
    assert len(store) == 0


def test_defaults_are_bounded():
    """A default store ships with both guards on, so it is never unbounded."""
    store: SessionStore[str] = SessionStore()
    assert store._ttl == DEFAULT_SESSION_TTL_SECONDS
    assert store._max == DEFAULT_MAX_SESSIONS
    assert DEFAULT_MAX_SESSIONS == 1_000
    assert DEFAULT_SESSION_TTL_SECONDS == 2 * 60 * 60


def test_ttl_expires_idle_session():
    clock = FakeClock()
    store: SessionStore[str] = SessionStore(ttl_seconds=100, clock=clock)
    sid = store.create("s")

    clock.advance(100)  # exactly at the TTL -> still alive (boundary is inclusive).
    assert store.get(sid) == "s"

    clock.advance(101)  # now past the TTL relative to the last access -> gone.
    assert store.get(sid) is None
    assert len(store) == 0


def test_get_slides_the_ttl_forward():
    """An actively polled session never expires; only its idle siblings do."""
    clock = FakeClock()
    store: SessionStore[str] = SessionStore(ttl_seconds=100, clock=clock)
    active = store.create("active")
    idle = store.create("idle")

    # Keep touching `active` every 80s across a span well beyond one TTL.
    for _ in range(5):
        clock.advance(80)
        assert store.get(active) == "active"

    # `idle` was never touched again, so it lapsed; `active` survived via sliding refresh.
    assert store.get(idle) is None
    assert store.get(active) == "active"


def test_purge_expired_reports_count_and_is_lazy():
    clock = FakeClock()
    store: SessionStore[str] = SessionStore(ttl_seconds=10, clock=clock)
    store.create("a")
    store.create("b")
    clock.advance(5)
    store.create("c")  # younger than a/b

    clock.advance(6)  # a, b are now 11s idle (expired); c is 6s idle (alive).
    assert store.purge_expired() == 2
    assert len(store) == 1
    assert store.purge_expired() == 0  # idempotent once swept.


def test_ttl_none_disables_expiry():
    clock = FakeClock()
    store: SessionStore[str] = SessionStore(ttl_seconds=None, clock=clock)
    sid = store.create("forever")
    clock.advance(10_000_000)
    assert store.get(sid) == "forever"
    assert store.purge_expired() == 0


def test_max_size_evicts_least_recently_used():
    store: SessionStore[int] = SessionStore(max_sessions=3, ttl_seconds=None)
    ids = [store.create(i) for i in range(3)]

    # Touch the oldest so it is no longer the LRU victim.
    assert store.get(ids[0]) == 0

    # A 4th create overflows the cap; the LRU entry (ids[1]) is evicted, not ids[0].
    ids.append(store.create(3))
    assert len(store) == 3
    assert store.get(ids[1]) is None  # evicted (was least-recently-used)
    assert store.get(ids[0]) == 0  # protected by the recent access
    assert store.get(ids[2]) == 2
    assert store.get(ids[3]) == 3


def test_max_size_holds_under_a_flood():
    store: SessionStore[int] = SessionStore(max_sessions=50, ttl_seconds=None)
    for i in range(500):
        store.create(i)
    assert len(store) == 50  # capped no matter how many were minted.


def test_invalid_max_sessions_rejected():
    with pytest.raises(ValueError):
        SessionStore(max_sessions=0)


def test_session_environment_bounds_require_positive_finite_values(monkeypatch):
    monkeypatch.setenv("TEST_CAT_TTL", "90.5")
    monkeypatch.setenv("TEST_CAT_CAP", "250")
    assert _positive_env_float("TEST_CAT_TTL", 1) == 90.5
    assert _positive_env_int("TEST_CAT_CAP", 1) == 250

    for bad in ("0", "-1", "nan", "inf", "not-a-number"):
        monkeypatch.setenv("TEST_CAT_TTL", bad)
        with pytest.raises(ValueError, match="positive number"):
            _positive_env_float("TEST_CAT_TTL", 1)

    for bad in ("0", "-1", "1.5", "not-a-number"):
        monkeypatch.setenv("TEST_CAT_CAP", bad)
        with pytest.raises(ValueError, match="positive integer"):
            _positive_env_int("TEST_CAT_CAP", 1)


def test_thread_safety_under_concurrent_creates():
    """Concurrent writers must not corrupt the store or exceed the cap."""
    cap = 64
    store: SessionStore[int] = SessionStore(max_sessions=cap, ttl_seconds=None)

    def worker(base: int) -> None:
        for i in range(200):
            sid = store.create(base + i)
            store.get(sid)

    threads = [threading.Thread(target=worker, args=(t * 1000,)) for t in range(8)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    # 1600 creates total, but the cap holds and the structure is intact.
    assert len(store) == cap


def test_transaction_serializes_same_session_and_releases_after_exception():
    store: SessionStore[dict[str, int]] = SessionStore(ttl_seconds=None)
    sid = store.create({"value": 0})
    start = threading.Barrier(3)
    overlap = threading.Barrier(2)
    guard = threading.Lock()
    active = 0
    max_active = 0

    def worker() -> None:
        nonlocal active, max_active
        start.wait()
        with store.transaction(sid) as session:
            assert session is not None
            with guard:
                active += 1
                max_active = max(max_active, active)
            try:
                # Same-session callers cannot rendezvous here: one times out, then the
                # queued caller enters after the first transaction releases its lock.
                overlap.wait(timeout=0.15)
            except threading.BrokenBarrierError:
                pass
            session["value"] += 1
            with guard:
                active -= 1

    threads = [threading.Thread(target=worker) for _ in range(2)]
    for thread in threads:
        thread.start()
    start.wait()
    for thread in threads:
        thread.join(timeout=2)
        assert not thread.is_alive()

    assert max_active == 1
    assert store.get(sid) == {"value": 2}

    with pytest.raises(RuntimeError, match="probe"):
        with store.transaction(sid):
            raise RuntimeError("probe")
    with store.transaction(sid) as session:
        assert session == {"value": 2}


def test_transactions_for_different_sessions_run_in_parallel():
    store: SessionStore[str] = SessionStore(ttl_seconds=None)
    ids = [store.create("a"), store.create("b")]
    start = threading.Barrier(3)
    overlap = threading.Barrier(2)
    entered: list[str] = []

    def worker(sid: str) -> None:
        start.wait()
        with store.transaction(sid) as session:
            assert session is not None
            entered.append(session)
            overlap.wait(timeout=1)

    threads = [
        threading.Thread(target=worker, args=(sid,))
        for sid in ids
    ]
    for thread in threads:
        thread.start()
    start.wait()
    for thread in threads:
        thread.join(timeout=2)
        assert not thread.is_alive()

    assert sorted(entered) == ["a", "b"]
    assert overlap.broken is False


def test_borrowed_session_survives_ttl_and_lru_until_transaction_finishes():
    clock = FakeClock()
    store: SessionStore[str] = SessionStore(
        ttl_seconds=10,
        max_sessions=2,
        clock=clock,
    )
    borrowed = store.create("borrowed")
    idle = store.create("idle")

    with store.transaction(borrowed) as session:
        assert session == "borrowed"
        clock.advance(11)
        assert store.purge_expired() == 1  # the idle sibling expires
        assert len(store) == 1  # the borrowed session remains pinned past its TTL
        replacement = store.create("replacement")
        assert len(store) == 2

    # Access was linearized when the transaction acquired its lock, so once no request
    # borrows it the old session is again eligible for the existing lazy TTL sweep.
    assert store.purge_expired() == 1
    assert store.get(borrowed) is None
    assert store.get(replacement) == "replacement"
    assert store.get(idle) is None


def test_entry_owned_lock_count_stays_within_session_cap_and_missing_ids_add_none():
    cap = 8
    store: SessionStore[int] = SessionStore(max_sessions=cap, ttl_seconds=None)
    for value in range(50):
        store.create(value)
    for value in range(50):
        assert store.get(f"missing-{value}") is None
        with store.transaction(f"missing-{value}") as session:
            assert session is None

    assert len(store) == cap
    assert len({id(entry.transaction_lock) for entry in store._sessions.values()}) == cap


def test_all_borrowed_cap_and_delete_fail_fast_then_recover_without_overshoot():
    store: SessionStore[str] = SessionStore(max_sessions=1, ttl_seconds=None)
    original = store.create("original")

    with store.transaction(original) as session:
        assert session == "original"
        with pytest.raises(SessionCapacityError, match="slots.*busy"):
            store.create("blocked")
        assert store.delete(original) is False
        assert len(store) == 1
        assert len(store._sessions) == 1

    replacement = store.create("replacement")
    assert len(store) == 1
    assert store.get(original) is None
    assert store.get(replacement) == "replacement"
    assert len({id(entry.transaction_lock) for entry in store._sessions.values()}) == 1
