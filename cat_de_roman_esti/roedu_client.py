"""roedu_client — the RO-EDU data-platform client for this app.

Since 2026-07-25 this is a thin re-export of the **canonical** client, which the
producer owns because it defines the `/v1` contract (romania_scraper ADR-0069).
The implementation lives in the generated, stamped `_roedu_client_core.py`; this
module only keeps the historical import path stable:

    from cat_de_roman_esti.roedu_client import RoeduClient
    c = RoeduClient("http://localhost:8077", api_key="cat-de-roman-dev")
    for node in c.iter("kg_nodes", category="istorie"):
        ...
    for edge in c.iter("kg_edges", src_id=node_id):
        ...

Config via env:
    ROEDU_API_URL   (default http://localhost:8077)
    ROEDU_API_KEY   (this app uses "cat-de-roman-dev")

Still stdlib-only and still fail-closed: a page reporting ``available=false``
stops the iteration rather than fabricating data. Adopting the canonical core
additionally fixed a real defect this app's own copy had — iteration now refuses
a **repeated pagination cursor** instead of looping forever on a broken or
hostile server.

To change client behaviour, edit the canonical file in romania_scraper and re-run
`scripts/sync_roedu_client.py --write`; never edit `_roedu_client_core.py` here.
"""

from __future__ import annotations

from ._roedu_client_core import RoeduClient, RoeduContractError

__all__ = ["RoeduClient", "RoeduContractError"]
