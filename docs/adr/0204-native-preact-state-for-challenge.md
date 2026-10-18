# ADR-0204: native Preact state for Alchimie Challenge

Status: Accepted and M3-qualified at9c44d01f; M4 remains separate.
Date: 2026-10-18
Authority: orchestrating agent under PROGRAM E8/E10 and the requested efficient game migration.

## Context

The unqualified M3 direction in ADR-0202/S1 selected Signals. Its current adapter
returns ordinary render snapshots and stable setters for20 local state fields;
no computed value, Signal DOM binding or independent reactive observer is used.
It therefore rerenders the whole Challenge component while adding a browser
runtime. The approved score split passes the original tests but leaves the route
2,960 gzip bytes above its unchanged40,960-byte limit.

## Decision

Use native `useState` from `preact/hooks` for those local snapshots, consistently
with the other game screens and the original state model. Supersede only the
earlier unqualified Signals implementation direction, not the functional gates.

Installed Preact11 records successive setter values immediately in its pending
hook state and deduplicates the component in its microtask render queue. The
three existing batch callbacks are synchronous. Remove their wrapper only,
preserving every statement and its order; do not create another batching engine.
This is specific to these render snapshots, not a replacement for general
Signals observers or transactions.

Preserve ownership/lifetime refs, native drag/drop, focus, saved-game recovery,
score/privacy behavior, motion and all existing assertions. Source-frozen API
and helper rules remain, except the separately approved ADR-0203 score split.
Keep dependency/tool pins unchanged during this source qualification.

## Consequences

Require original score tests, held-action/reentry, replay/reset, focus and native
drag/drop journeys, plus complete route JS/CSS measurements. Keep failure packets.
Clean unit/full, exact PNGs, CSP/vitals and independent review remain mandatory
before M3/M4 acceptance. Never relax a cap or assertion to admit this revision.

## Qualification — 2026-10-19

Exact source9c44d01f passes unit27/full37, original9PNG/Axe/vitals/CSP and
independent M3 acceptance; locally landed under ADR-0199. The
[qualification record](../reviews/gui-m3/qualification.json) binds actual evidence.
