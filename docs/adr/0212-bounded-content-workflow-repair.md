# ADR-0212: Bounded repair of the content workflow

Date: 2026-10-25
Status: accepted; implementation independently qualified locally, executable next-wave plan pending

## Context

Paul approved: “Yes, proceed with the workflow repair, up to 8 ticks and 6 local commits.
Remove duplicate work, preserve the quality checks and existing budgets, then continue
autonomously.” The exact approval and proposed scope are retained in content-loop scratch as
WORKFLOW_REPAIR_OWNER_OVERRIDE.json and repair/r1/approval-record.json. This supersedes only
ADR-0211's execution/cadence and Class-P retained-world clauses; its content-quality rules remain.

The run had ten blocked and four closed waves with no qualified V2 content packet. Repeated
helper/read-contract work failed before candidate validation. Two existing implementation designs
are retained; the materializer design's placeholder overwrite remains a recorded provenance defect.
The already spent five successor-planning ticks and every prior failed-wave budget/wait remain.

Independent source review established that contentrails Audit includes current games_pack and
board_rankings bindings. behaviourView retains them and ConfirmFinal compares them with a fresh
audit. Therefore ADR-0211's instruction to change the pack/rankings but retain the old signed
world audit cannot satisfy the unchanged default all --check contract.

## Decision

- Authorize one shared repair account r1: at most eight productive ticks and six local commits.
  Preserve old accounts, holds, evidence and five carried planning ticks. No resets or new
  automatic repair accounts; content waves still have 24 ticks and 20 commits.
- Use the two completed designs to implement one separately versioned helper/runner bundle.
  Fresh independent Codex APP code review, meaningful historical real-output parity and refusal
  regressions, and an exact version pin precede production use. Preserve original helpers and
  the original manifest; new pins reference their parent baseline and actual review/test bytes.
- Check paths, permissions, schemas and complete output encoding before freezing. Generate exact
  hashes/action records mechanically. Draft code may change until frozen; signed/frozen evidence
  never changes. An immutable input bundle is referenced by digest rather than repeatedly copied.
- Read saved state first. An unchanged active canonical APP job returns a quiet pending result;
  do not redispatch or reread large histories. Reread full instructions on changed digest/missing
  context and the exact step for productive work. Actual native/content checks remain fresh.
- Shared technical blockers stop all dependent lanes. No extra general planning or negative-
  conclusion review stage is required before a concrete implementation or executable wave plan.
- Class P skips only KG apply4a. Both P and G rebuild, independently review, audit and re-sign
  quick, world and extensions under the new authored source, then replace all three authorities.
  Exact unchanged item judgments may follow the existing inherited-item rule; the world audit
  and final acceptance are fresh. No binding is stripped and no native validator is changed.
- Working helper/critic/factual/quality/verification roles use fresh Codex APP contexts and native
  dispatch/action/research evidence. Preserve fixed content identities, both fresh whole-batch
  rounds, seals, whole-author URL novelty, signatures before peer access/unseal and all source,
  native, corpus, HTTP, fuzzy, exact-SHA and pin gates. Missing B4 evidence and incomplete M2
  remain unresolved until actually satisfied; metadata reuse is never a qualification shortcut.
- Routine go/drop is recorded under standing owner delegation, with item-specific holds retained.
  Queue fully qualified UNLANDED packets with exact HEAD/dependencies and continue autonomously.
  A successor may use only exact qualified predecessor HEAD or explicit clean main, retaining
  the original main anchor and fresh checks. Unqualified repair/code is never a base.
- Claude is only final consolidated end-of-run/prelanding review when Paul stops or requests it.
  This loop never lands, merges, pushes, fetches, changes remote refs, deploys, deletes or prunes.
  Runtime, GUI, dependencies, toolchain, CI, model/cache settings and bound rubric stay unchanged.

## Qualification

Implementation qualification (2026-10-25): fresh independent APP review accepted the exact
workflow-r1-v2 bundle after 70/70 real historical-output, normalization and refusal regressions;
native validate-pack was GREEN, strict critique had zero failures/warnings, and docs/whitespace
checks passed. Review evidence is retained under content-loop scratch `repair/r1/review02/`;
the separate pin is `miner/versions/workflow-r1-v2.pin.json` (SHA-256
`19892669c8a0a1980f12725f63e3239c80b9949fbd9b88a5f46c82d8385fb710`).
The original 101 helper files and baseline manifest remained exact; the first rejected version
and reviewer-harness preparation failure remain preserved. This qualifies reusable tooling and
the reviewed procedure, not content, future role isolation or native Cald feedback parity.
One executable next-wave plan and its independent review remain pending. Preserve five carried
planning ticks and every old budget/hold; report any residual conflict with the 24/20 content cap.
