# ADR-0116: Share reviewed current-content test expectations

- Status: accepted
- Date: 2026-09-07

## Context

V82's small content additions required many copies of current artifact hashes and counts
to change. Missed copies and seed-dependent fixtures caused repeated full-gate failures
without identifying a gameplay defect. Historical invariants still require independent
fixed evidence; replacing expected values with values read from the fixture would hide drift.

## Decision

Keep one manually authored, immutable `tests/current_content.py` snapshot for genuinely
current artifact hashes, payload hashes and inventories. Existing assertions retain their
meaning and compare actual content with this expected snapshot. Do not derive expectations
from the fixtures being tested. Update the snapshot only after independently checking the
reviewed delta and preservation of earlier content.

Historical wave, candidate, critique, pre-apply, ledger and reconstruction hashes remain
with their owning tests. A historical-looking variable name is not sufficient classification:
follow what the assertion actually compares. The V83 refactor was checked against the V82
baseline before any content mutation; expected values remain equivalent.

Public journey tests whose purpose is to exercise a named round may find a bounded current
seed for that target through the normal picker, then exercise the real API. Keep separate
reviewed seed/date snapshots for selection contracts. Do not rewrite old review archives
when a later content batch changes which target a seed selects, and do not silently skip
behavioral coverage because an incidental seed changed.

Reload assertions bind to an API request issued after the main frame navigates and consume
that response before further navigation. A recovery GET already in flight from the old
document is not proof that the new page resumed correctly. This boundary repairs an observed
response-body race while preserving the actual state comparison and existing time limits.

## Consequences

New batches update one current snapshot while retaining exact historical reconstruction.
This reduces duplicated maintenance, not the strength or scope of verification. The
independent V83 pin-refactor review records AST/value equivalence and immutability checks.
