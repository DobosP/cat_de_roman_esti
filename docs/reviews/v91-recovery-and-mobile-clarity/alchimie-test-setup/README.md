# Alchimie hint-recovery test setup

Valid until: final V91 verification supersedes this focused record — then treat as history.

The initial full browser run passed 338 cases and failed the two Alchimie output-clue
cases. Its generic hint-unlock setup tried arbitrary seed pairs. The revised Sport board
made one of those pairs productive, so the server correctly returned a category clue
when the target was one action away. Root retains that original full-run evidence.

This correction changes only `frontend/e2e/solutions.py` and
`frontend/e2e/alchimie-action-recovery.spec.mjs`. The test-process helper derives 11 unique
owned-input pairs with no recipe in the private projection. A cursor advances through
distinct pairs across hint stages. Each setup POST asserts an empty discovery list,
unchanged inventory, no repeated attempt and an unfinished game.

Output, pair and category clues each have a lost-response case. The category case first
performs the existing productive step. All three check exact paid-cue retention through
GET and reload, hint charges, selection state, hidden target ID and the appropriate
hint/output shape. The target label was already public; the test does not claim otherwise.
No runtime, backend, data, generated static or seeded-start file changed.

Before/after capture compares all six games' existing `initial`, `steps` and `practice`
values: all 18 comparisons are exact. Only Alchimie's test-only `hint_setup` field is
added. Its inputs are already-owned seed IDs; no target/output IDs, recipes or routes
are added to that field, and it is never bundled or sent to browser storage.

Focused browser verification passed **34 cases**, desktop and emulated mobile, exit 0,
without retries, in 2.0 minutes. All **30 bound inputs** stayed exact across that run.
Ruff and whitespace checks passed. The isolated BFF exited with the suite; port 8188
had no remaining server process. [Independent review](independent-review.json) accepts
the two-file change with no findings and distinguishes its checks from the browser gate.

[The manifest](manifest.json) binds [the deterministic gzip archive](evidence.tar.gz):
before/after helper output, equality comparison, original source copies, focused logs,
screenshots, input hashes and independent review. Every archived entry, hash, size and
the zero gzip timestamp were verified. Root owns the refreshed full frontend matrix and
final local V91 landing.
