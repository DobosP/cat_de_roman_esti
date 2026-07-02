# ADR-0002: Conform exactly to the canonical KG contract v1

Date: 2026-06-21
Status: accepted
Supersedes: none

## Decision
Adopt the owner-supplied **Romanian Knowledge Graph canonical contract v1** as the
single data-layer authority for this repo. [`docs/KG_CONTRACT.md`](../KG_CONTRACT.md)
is the authoritative record (pasted verbatim from the platform owner); this repo is a
pure **consumer** and conforms exactly to the served record shapes — `kg_nodes` /
`kg_edges` / `kg_puzzles` with the four difficulty levers encoded as data (hop
distance, concept obscurity, edge visibility/hints, distractor density). The producer
side (`romania_scraper`) owns the build; `ro_data_server` serves it.

## Context / why
Introduced with v1 of the game (`e864405`, 2026-06-21). The game must run identically
against a live `ro_data_server` and the bundled offline fixture, so both must share
one frozen record shape; a consumer-side schema fork would silently desynchronize the
fixture, the validator (`scripts/validate_fixture.py`), and live play. Why not define
a repo-local schema: the contract is cross-repo (producer, server, this consumer, and
the mobile app-pack ingest all cite it) — only an owner-level contract keeps them
aligned.

## Consequences
- Any schema change is a **contract v2** decision made at the platform level, not
  here; this repo never extends or reinterprets record fields unilaterally.
- The offline fixture, `scripts/validate_fixture.py` (13 invariant classes), and the
  app-pack contract tests all enforce contract conformance in CI.
- `docs/KG_CONTRACT.md` stays in place as the full normative text; this ADR only
  numbers the decision to adopt it.
