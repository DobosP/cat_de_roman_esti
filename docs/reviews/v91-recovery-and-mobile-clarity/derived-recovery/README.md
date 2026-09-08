# Intrusul and Perechi owned recovery

Valid until: V91 final verification supersedes these development observations — then treat as history.

Baseline: clean local main `e2e03638b90fc9248c33f70eedaa8c9c5fbd87ad`, served directly
from its existing V90 source/static by an isolated BFF on port 8188. The task worktree
was not built for this baseline. [The manifest](baseline-manifest.json) binds every static
file and the 36 artifacts in [the deterministic gzip archive](baseline-evidence.tar.gz).
The JSON inside binds both screen sources, the owner helper, manifest and HTML too.

## Actual baseline findings

The completed browser runner captured 22 journeys over both games, then two separate
actual-unmount contrasts and one productive Perechi match: 25 observations total. Browser
routes first let the real BFF commit, then substitute a 503 or hold the response. Reads
reach the BFF except explicitly documented 503/404/wrong-identity fault injection. The
JSON records public responses, storage, counters and visible controls; screenshots show
390px layouts. Private solution lookup runs only in the test process.

| Observation | Intrusul | Perechi |
|---|---|---|
| Lost wrong guess/match, paid hint, win and loss | Existing GET restores state; terminal score recorded once | Same |
| Lost productive nonterminal match | Not applicable | Existing GET restores one pair and six remaining tiles |
| Paid clue after lost response | Existing clue visible; hints_used 1 | Existing hint visible; hints_used 1 |
| Failed verification after committed hint | Four tiles and hint re-enabled; no GET-only retry | Eight tiles and hint re-enabled; no GET-only retry |
| Held winning POST after another tab saves a round | Old terminal adopted; played 1; foreign pointer survives | Same |
| Held recovery GET after another tab saves a round | Old terminal adopted and recorded | Same |
| Held 404 after another tab saves a round | Old board unlocked; foreign pointer survives | Same |
| Owned 404 | Old board and pointer retained | Same |
| GET with a wrong game_id | Public state adopted without identity rejection | Same |
| Exit, then immediate held win release | Old terminal recorded during departure | Same |
| Wait for actual unmount before held win release | No score recorded; pointer preserved | Same |

The last two rows distinguish an exit-animation race from actual post-unmount behavior.
The initial wrong Intrusul hint locator was interrupted; its original script/error log
are retained and excluded from successful observations. The corrected script uses the
actual “Arată indiciul” control. No double-charge or missing-backend-clue claim follows.

The runner's attempted session DELETE returned 405 because that route is unsupported.
The isolated in-memory BFF was stopped after capture, discarding all its sessions. No
persistent session or shared-main file was written. The manifest records that limitation.

Before: [Perechi failed verification](baseline-perechi-failed-read.png),
[Intrusul failed verification](baseline-intrusul-failed-read.png),
[stale Perechi win](baseline-perechi-late-mutation-pointer.png),
[stale Intrusul win](baseline-intrusul-late-mutation-pointer.png).

## Implementation and verification

[ADR-0138](../../../adr/0138-owned-intrusul-perechi-recovery.md) records the bounded
screen changes. Both screens reuse the existing owner with GET-only manual retry,
identity/pointer checks and synchronous exit invalidation. Recovery keeps tiles, hints
and selection clearing locked, hides the normal next-move prompt, and visibly offers
verification or loading the current saved round. Perechi also binds deferred focus to
the accepted game and pointer. No backend or content files change in this lane.

Development typecheck, focused lint and 26 native checks passed. The initial candidate
passed all 72 then-defined browser variants and 22 repeated baseline observations;
32 source/static inputs stayed exact. [Its manifest](initial-candidate-manifest.json)
binds [the raw archive](initial-candidate-evidence.tar.gz). Screenshot review found
ordinary “Atinge…” feedback below a changed-pointer notice, so the final screen hides
normal guide and feedback text while recovery is active.

Independent review then reproduced a P2 in both games: after a committed win and failed
GET, another tab deletes the saved pointer before manual retry. The retry took the
helper's initial null-storage fallback and recorded the old win. Retaining the original
savedId in the pending snapshot fixes this; a newly begun retry ticket must match it
before any GET. Independent static re-review accepted that change. The original two
Back-navigation probes passed; they were observations at one timing, not proof that the
whole departure interval was safe. [Review findings](review-findings-manifest.json) bind
[the original scripts, captures and screenshots](review-findings-evidence.tar.gz).

The next 80-case desktop/mobile run completed with 76 passes and four Back failures:
both games could record the held winning reply during animated departure. Its complete
summary and all traces are retained in [the third-candidate archive](third-candidate-evidence.tar.gz),
with [exact inputs and outcome](third-candidate-manifest.json). The runner returned 143
after that complete summary; the cause of 143 is unestablished. This is a red receipt,
never a passing gate. All 32 bound source/static inputs stayed exact. Six accompanying
state captures passed and showed locked recovery without stale ordinary feedback.

The bounded correction uses screen presence to invalidate action ownership in a layout
effect at departure, clears Perechi focus, and blocks action/score effects while leaving.
No App or shared helper change is part of that correction.

## Final focused result

The final candidate passed all **80 browser variants** (40 logical cases across desktop
and emulated mobile) in 4.5 minutes, exit 0, with no retries. The four formerly failing
Back cases also passed a prior focused run, exit 0, in 27.9 seconds. Six final state
captures show no enabled mutations or stale tap feedback during uncertainty and no
adopted/scored old terminal after a pointer change. All **42 bound source, data, seeded
start and static inputs stayed exact** across the full run. Typecheck, focused lint and
26 native checks passed. [Final receipt](final-candidate-manifest.json) binds
[all raw logs, captures, screenshots and input hashes](final-candidate-evidence.tar.gz).
The isolated BFF exited with the suite; port 8188 had no remaining server process.

[Independent final review](independent-final-review.json) accepts the bounded changes:
four exact Back regression variants and two pointer-removal-between-retries cases pass,
with **39 source/static/data pins unchanged**. The reviewer found no remaining issue.
[Its archive manifest](independent-final-manifest.json) binds
[all original and final independent artifacts](independent-final-evidence.tar.gz),
including the earlier counterexamples and timing-dependent Back observations.

After: [Perechi read-only recovery](final-perechi-failed-read.png),
[Intrusul read-only recovery](final-intrusul-failed-read.png),
[Perechi changed-pointer recovery](final-perechi-late-mutation-pointer.png),
[Intrusul changed-pointer recovery](final-intrusul-late-mutation-pointer.png).

These focused checks are browser emulation and local BFF verification. Root owns the
complete integration matrix, final evidence seal and local V91 landing.

[The archive verifier](verify-evidence.py.txt) checks deterministic gzip headers, complete
entry sets, entry hashes and sizes, and archive hashes without extracting into the repo.
