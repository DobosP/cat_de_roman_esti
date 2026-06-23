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
    SessionStore,
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
    assert DEFAULT_MAX_SESSIONS is not None and DEFAULT_MAX_SESSIONS >= 1
    assert DEFAULT_SESSION_TTL_SECONDS > 0


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
