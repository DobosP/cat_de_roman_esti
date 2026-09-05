# ADR-0102: Pack-only content-wave workflow

- Status: accepted
- Date: 2026-09-06

## Context

Some curated game instances can use the served KG unchanged. The generic importer has a
`--skip-merge` path, but it also accepts node and edge input, which could make an
instance-only author accidentally omit reviewed topology.

## Decision

`scripts/import_candidates.py --pack-only` is the instance-only import mode. It performs
the normal complete factual/quality preflight and rejects nonempty `nodes` or `edges`
before opening the file transaction. `--skip-merge` remains available for an already
merged graph. The review and promotion bindings remain those in ADR-0023.

## Consequences

Pack-only waves use the shared importer and review/apply tooling; they do not introduce a
versioned apply script. A pack change still refreshes digest-bound ranking, derived, and
mobile artifacts, while a frozen derived-source payload stays governed by its source pin.
