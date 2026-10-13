# Cat lighter gates (PROGRAM E10)

Branch: `fix/gui-cat-lighter-gates`
Session: Codex GUI programme continuation, 2026-10-13
Worktree: `/home/dobo/work/_worktrees/cat_de_roman_esti/fix__gui-cat-lighter-gates`

## 1. Purpose / Big Picture

Reduce repeated qualification work without removing any assertion. A full can reuse
verified lanes from its clean same-SHA unit. Frontend iterations can reuse native
race evidence only when every input of the reused tests remains identical.

## 2. Progress

- [x] 2026-10-13T07:25Z: Read handover, E10, loop and repository instructions; create branch from c352ff4205231a1728355e886003a5301bf66701.
- [x] 2026-10-13T07:30Z: Independently inspect wrapper persistence and native read dependencies.
- [x] 2026-10-13T07:41Z: Implement reuse, 64 focused cases and bounded browser workers; first pinned shell passes; independent source review resolved all findings.
- [ ] Run cheap checks, independent review, clean unit and one full; record timings.
- [ ] Publish the feature branch and update the programme ledger.

## 3. Surprises & Discoveries

The wrapper preserves other targets in its rolling mirror but deletes the current
target. Inner SDK and wrapper invocation UUIDs differ; bootstrap evidence joins
them. Compose forwards GOMAXPROCS but does not forward GATE_PARALLEL_MAX. Native
tests read content evidence under docs and four frontend files, so excluding all
docs/frontend bytes would be unsafe.
Actual Go test variants repeat Imports; the parser now normalizes those edges.
The first clean unit passed 27 checks, but contentrails consumed 1,123.73 seconds.
An independently audited source-based exception is required for useful warm reuse.

## 4. Decision Log

2026-10-13: Reuse real completed evidence, with hashes and source/toolchain bindings,
and execute the original commands on a missing or invalid proof. Retain source
and command evidence in the consuming result. Read the committed parallel cap and
honor the wrapper's lower per-run limit. Authority: PROGRAM E10 / Cat ADR-0199.

2026-10-13: Keep dynamic dependency closure as default; exempt only contentrails
under the independently recomputed 238-file native source signature. Bind all
Markdown and generated native-looking reader inputs. Any changed code signature
forces original execution; the fresh whole serving/API suites remain mandatory.

## 5. Outcomes & Retrospective

Clean qualification pending. Pinned-shell diagnostic checks passed 64 cases and
documentation checks; final patched verification precedes the commit. Prior unit was 20.8 minutes and full
34.5 minutes (accepted c9017b5b evidence); no improvement is claimed yet.

## 6. Context and Orientation

`scripts/gui-repo-hook.mjs` calls nativeUnit during both unit and full. The kit SDK
binds execution actions/logs into `.gate/<target>/result.json`. The wrapper verifies
the source and protected files after the task. `frontend/playwright.gui.config.mjs`
currently restricts full browsers to two workers despite the four-worker cap.

## 7. Plan of Work

Validate same-SHA unit evidence, retain and reuse its seven expensive lanes, keep
fresh build/identity/budget/source checks, and retain a bounded previous native
proof for frontend iterations. Current generated-asset consumers still execute.
No baseline, content, limit, lockfile or kit bytes change.

## 8. Concrete Steps

From this worktree run the committed gate wrapper with literal HEAD: `unit`, then
`python3 -I scripts/gui-full-runner.py --sha <full SHA>`. Cheap checks use the pinned
Linux context. Run `git diff --check` and the two established documentation checks.

## 9. Validation and Acceptance

Negative controls reject changed source/toolchain/lock/CSP, failed or dirty results,
missing/duplicate checks, tampered commands/logs, and unsafe paths. Worker limits
honor four and lower limits. Qualification preserves all existing unit/full checks,
933 browser cases, nine exact PNGs, PG, CSP, axe, vitals and parity. An independent
review must verify bindings and evidence before the ledger row closes.

## 10. Idempotence and Recovery

One gate and one writer per worktree. Missing evidence executes original commands;
fresh wrappers discard caches. Keep a single rolling proof and remove only owned
superseded scratch after preserving compact result hashes. Never alter live source
during a gate, overwrite canonical keepers or clean another session's resources.

## 11. Artifacts and Notes

Actual results live in `.gate/unit/result.json` and `.gate/full/result.json`.
Record command, literal SHA, duration and SHA-256 after each actual run. Operator:
agent:codex (PROGRAM E8). No runtime or acceptance result exists for this branch yet.

## 12. Interfaces and Dependencies

Core-v1.9 stays selected. New Cat helpers consume its existing result, execution and
bootstrap schema; no published kit changes. Feature-branch pushes are authorized;
app-main pushes and production remain Paul-only.
