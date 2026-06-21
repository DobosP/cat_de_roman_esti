"""roedu_client — tiny, dependency-free client for the RO-EDU data platform.

Vendored (verbatim-in-spirit) from ``/home/dobo/work/roedu/client/roedu_client.py``.
Stdlib only (urllib), so it vendors cleanly into any consuming app without adding a
dependency. Talks to ``romania_scraper.dataapi`` over HTTP (via ``ro_data_server``),
handles cursor pagination, and trusts the platform's license gate — the server is
fail-closed, and so is this client: any page reporting ``available=false`` stops the
iteration immediately rather than fabricating data.

    from cat_de_roman_esti.roedu_client import RoeduClient
    c = RoeduClient("http://localhost:8077", api_key="cat-de-roman-dev")
    for node in c.iter("kg_nodes", category="istorie"):
        ...
    for edge in c.iter("kg_edges", src_id=node_id):
        ...

Config via env when vendored into an app:
    ROEDU_API_URL   (default http://localhost:8077)
    ROEDU_API_KEY   (cat_de_roman_esti uses "cat-de-roman-dev")
"""

from __future__ import annotations

import json
import os
import urllib.parse
import urllib.request
from collections.abc import Iterator


class RoeduClient:
    def __init__(
        self,
        base_url: str | None = None,
        api_key: str | None = None,
        *,
        timeout: float = 30.0,
    ) -> None:
        default_url = os.environ.get("ROEDU_API_URL", "http://localhost:8077")
        self.base_url = (base_url or default_url).rstrip("/")
        self.api_key = api_key or os.environ.get("ROEDU_API_KEY", "")
        self.timeout = timeout

    def _get(self, path: str, params: dict | None = None) -> dict:
        url = f"{self.base_url}{path}"
        if params:
            clean = {k: v for k, v in params.items() if v is not None}
            url += "?" + urllib.parse.urlencode(clean)
        headers = {"X-API-Key": self.api_key, "Accept": "application/json"}
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=self.timeout) as resp:  # noqa: S310
            return json.loads(resp.read().decode("utf-8"))

    def health(self) -> dict:
        return self._get("/v1/health")

    def products(self) -> list[dict]:
        return self._get("/v1/products")

    def page(self, product: str, *, cursor: str | None = None, limit: int = 200, **filters) -> dict:
        params = {"cursor": cursor, "limit": limit, **filters}
        return self._get(f"/v1/products/{product}", params)

    def iter(
        self, product: str, *, limit: int = 200, max_records: int | None = None, **filters
    ) -> Iterator[dict]:
        """Yield every record of a product, following cursors. Stops at max_records.

        Fail-closed: a page with ``available=false`` (gate refusal / store not built)
        ends the iteration without yielding partial or fabricated records.
        """
        cursor = None
        seen = 0
        while True:
            page = self.page(product, cursor=cursor, limit=limit, **filters)
            if not page.get("available", False):
                return
            for rec in page.get("records", []):
                yield rec
                seen += 1
                if max_records and seen >= max_records:
                    return
            cursor = page.get("next_cursor")
            if not cursor:
                return
