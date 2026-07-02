# ADR-0003: Mobile contract — stable operationIds + trust manifest

Date: 2026-06-29
Status: accepted
Supersedes: none

## Decision
Freeze a mobile-facing API contract on the BFF, additive over `/api/wordgames/*`:
(1) **stable OpenAPI operationIds** `<tag>_<endpoint-name>` (e.g. `contexto_guess`)
via `generate_unique_id_function`, so route refactors never churn generated client
method names; (2) **`GET /api/manifest`** — a deterministic offline-KG trust manifest
(`schema_version`, `build_version`, content hash over sorted records, counts) that
lets a mobile app detect drift between its bundled KG copy and the server; (3) the
**hidden-answer invariant**: no public response leaks a game's secret before the
win/lose state. [`docs/MOBILE_CONTRACT.md`](../MOBILE_CONTRACT.md) is the
authoritative spec; `scripts/export_openapi.py` exports the schema offline.

## Context / why
Landed in `125a357` (2026-06-29) for the Track A generated client (roedu-mobile
cat-mobile MVP). FastAPI's default operationIds bake in the HTTP path, which would
couple the generated TS client surface to route internals; and an offline-first
mobile app needs a cheap, deterministic way to verify its bundled fixture. Why not a
handwritten client: the fleet convention is generated, contract-tested clients
(`tests/test_mobile_contract.py`, manifest tests in `tests/test_app_pack_contract.py`).

## Consequences
- operationIds and manifest shape are **append-only**: renaming or removing one is a
  breaking contract change requiring a superseding ADR + client regeneration.
- Web and mobile clients build only on `/api/wordgames/*` + `/api/health` +
  `/api/manifest` (per ADR-0001 the removed `/api/games` never returns).
- Contract tests are regression guards on the reveal boundary of all four games.
