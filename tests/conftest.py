"""Shared test fixtures: a FAKE in-process RoeduClient (no live server).

The fake mimics the platform's page/cursor/availability contract over the bundled
KG sample, so the loader + engine are exercised exactly as they would be against the
real ``ro_data_server`` — including the fail-closed ``available=false`` path.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

FIXTURE = Path(__file__).parent / "fixtures" / "kg_sample.json"


@pytest.fixture(scope="session")
def kg_raw() -> dict:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


class FakeRoeduClient:
    """In-process stand-in for RoeduClient.

    Serves records out of an in-memory KG dict with real cursor pagination and
    per-product availability. ``blocked`` products report ``available=false`` (gate
    refusal), and ``iter`` over them must yield nothing.
    """

    def __init__(
        self,
        raw: dict,
        *,
        blocked: set[str] | None = None,
        page_size: int = 2,
        api_key: str = "cat-de-roman-dev",
    ):
        self._data = {
            "kg_nodes": list(raw.get("kg_nodes", [])),
            "kg_edges": list(raw.get("kg_edges", [])),
            "kg_puzzles": list(raw.get("kg_puzzles", [])),
        }
        self.blocked = blocked or set()
        self.page_size = page_size
        self.api_key = api_key
        self.calls: list[tuple[str, dict]] = []

    def health(self) -> dict:
        return {"ok": True, "service": "fake-ro-data-server"}

    def products(self) -> list[dict]:
        return [
            {
                "name": name,
                "available": name not in self.blocked
                and not (name.startswith("kg_") and self.api_key != "cat-de-roman-dev"),
            }
            for name in self._data
        ]

    def _filter(self, records: list[dict], filters: dict) -> list[dict]:
        out = records
        for key, val in filters.items():
            if val is None:
                continue
            out = [r for r in out if str(r.get(key)) == str(val)]
        return out

    def page(self, product: str, *, cursor=None, limit: int = 200, **filters) -> dict:
        self.calls.append((product, dict(filters, cursor=cursor, limit=limit)))
        if product in self.blocked or product not in self._data:
            return {"available": False, "records": [], "next_cursor": None}
        if product.startswith("kg_") and self.api_key != "cat-de-roman-dev":
            return {"available": False, "records": [], "next_cursor": None}
        records = self._filter(self._data[product], filters)
        start = int(cursor or 0)
        size = min(int(limit or self.page_size), self.page_size)
        chunk = records[start : start + size]
        nxt = str(start + size) if start + size < len(records) else None
        return {"available": True, "records": chunk, "next_cursor": nxt}

    def iter(self, product: str, *, limit: int = 200, max_records=None, **filters):
        cursor = None
        seen = 0
        while True:
            pg = self.page(product, cursor=cursor, limit=limit, **filters)
            if not pg.get("available", False):
                return
            for rec in pg.get("records", []):
                yield rec
                seen += 1
                if max_records and seen >= max_records:
                    return
            cursor = pg.get("next_cursor")
            if not cursor:
                return


@pytest.fixture
def fake_client(kg_raw):
    return FakeRoeduClient(kg_raw)
