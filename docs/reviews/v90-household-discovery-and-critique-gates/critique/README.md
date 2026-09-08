# V90 — directed Contexto critique floor

Valid until: the bound source, rubric or graph changes — then remeasure current behavior.

The numerical C3 gate is implemented under [ADR-0134](../../../adr/0134-directed-contexto-neighbor-floor.md).
Fewer than five unique existing non-distractor predecessors now blocks pending targets.
Approved records receive a warning for separate review. Direction is guess → target;
self-links, distractors, missing endpoints and outgoing-only edges contribute nothing.
Bidirectional edges count as traversable in both directions and parallel edges count once.
A count of five does not assess recognition, semantic legibility or existing A5 holds.

New Contexto dossiers carry the exact count and a sorted sample of at most ten labeled
predecessors. Their `recognition_assessed` value is false. Existing binding version1
continues to hash the new evidence and current rubric; archived dossiers use their own
embedded rubric digest. No archived dossier or historical rubric evidence was rewritten.

## Old-stock audit

The [implemented-code audit](implementation-audit.json) compares all242 existing Contexto
records with the clean `190d7fd` baseline. The new diagnostic changes **zero familiarity,
play-quality, pilot-score or eligibility profiles**. The ranker excludes `FAIL` findings;
it does not apply a generic warning penalty. No runtime or ranking formula changed.
These four approved records receive review proposals while remaining eligible:

| Record | Target | Unique incoming neighbors |
|---|---|---:|
| ct_geografie_030 | Lacul Roșu | 1 |
| ct_geografie_031 | Peștera Scărișoara | 2 |
| ct_istorie_309 | Abdicarea Regelui Mihai | 4 |
| ct_muzica_070 | B.U.G. Mafia | 4 |

Pending Shitpost238 and Industrie257 retain eight and thirteen incoming neighbors and their
existing pending status. Global pending strict critique checks all8 current pending rows:
zero item flags and zero failures;65 member-overuse and16 region inventory warnings remain.
This safeguard adds zero concepts, graph links, forms, lexical equivalents or rounds.

## Verification and limits

[verification.json](verification.json) binds exact sources, audits and lossless gzip logs
with decoded and archive SHA-256 values; gzip timestamps are zero. The pre-edit injection
and implemented-code audits are separate. [The baseline capture](baseline_audit.py.txt)
and [implementation comparison](implementation_audit.py.txt) preserve their actual code.

- Initial focused checks:15 passed. Initial Ruff found two assigned test lambdas;
  named functions fix those style findings without changing behavior.
- Combined critique/artifact/ranking behavior checks:163 passed,1 failed,2 deselected.
  The failure was an existing test's two-name warning allowlist; it now includes the
  new Contexto warning and still requires approved-stock findings to be WARN.
- Final focused checks:17 passed, including the corrected existing test. These cover
  0/4/5/11 incoming nodes, outgoing-only inflation, both bidirectional orientations,
  duplicate/distractor/self/missing-node edges, low-strength numerical counts,
  deterministic bounded evidence, strict CLI status behavior, promotion recheck,
  pending holds, real approved-stock score/eligibility isolation and archived binding.
- Ruff passes. Two generated-sidecar freshness checks and full integration remain with
  the orchestrator until its coherent rubric/default-pin/sidecar refresh is complete.
  The temporary stale sidecar state must never be served or landed; freshness checks
  remain strict. This subtask does not claim a complete V90 integration matrix.

Archived initial failures are retained as evidence. The new numeric check is not a
replacement for independent content judgment or Romanian-player playtesting.
