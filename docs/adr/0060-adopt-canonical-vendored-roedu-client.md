# ADR-0060: Adopt the canonical vendored RO-EDU client

Date: 2026-07-25
Status: accepted

## Context

This app carried its own private copy of `RoeduClient`. Comparing it against the
two other consumers (`ro_teacher`, `social_media_activities_app`) showed the five
transport methods (`__init__`, `_get`, `health`, `products`, `page`) were
**byte-identical in all three**, while `iter` had drifted into three variants.

Only `ro_teacher`'s variant guarded against the server repeating a pagination
cursor. **This app's copy did not** — a broken or hostile `ro_data_server` that
echoed one cursor would make `iter()` loop forever, fetching the same page
indefinitely.

The producer (`romania_scraper`) defines the `/v1` contract, so it now owns the
canonical client and vendors it (its ADR-0069).

## Decision

`cat_de_roman_esti/roedu_client.py` becomes a **thin re-export** of
`cat_de_roman_esti/_roedu_client_core.py`, a generated, stamped copy of the
canonical client produced by `scripts/sync_roedu_client.py --write` in
`romania_scraper`.

- The public import path is unchanged: `cli.py` and `__init__.py` keep doing
  `from .roedu_client import RoeduClient`.
- `_roedu_client_core.py` is **never edited here**. To change client behaviour,
  edit the canonical file in the producer and re-run the sync script.
- `tests/test_roedu_client_vendored.py` fails if the copy is hand-edited (the
  `VENDORED_SHA256` stamp digests the region between the BEGIN/END markers) and
  pins the behaviour this app depends on.

## Consequences

- **The infinite-loop defect is fixed**: iteration now raises
  `RoeduContractError` (a `ValueError` subclass, so any existing `except
  ValueError` still catches it) when a cursor repeats.
- A producer-side `/v1` change reaches this app by re-running one script instead
  of hand-porting a diff into three repos.
- This app gains `pages()`, which retains page-level `snapshot_id`/`release_id`
  metadata that `iter()` discards — unused here today, available if the KG lane
  ever needs release provenance.
- Still stdlib-only and still fail-closed on `available=false`; no new runtime
  dependency. The producer enforces stdlib-only with an AST test so the vendored
  file stays droppable into this app.
- Local behaviour changes are now visible as a failing drift test rather than a
  silent fork, which is the point.

Gate: backend 482/482 (was 477 before the 5 new client tests), whitespace clean.
