# ADR-0136: Recover uncertain Alchimie actions and one earned cue

Date: 2026-09-08
Status: accepted

## Decision

Alchimie combine, hint, reset and read-only verification share the existing synchronous
`gameActionRecovery` owner. Every failed mutation causes at most one GET of the same game,
with no automatic POST replay. A current ticket must still own the saved round before it
may adopt either a successful response or the verifying GET. Failed verification leaves a
persistent “Verifică jocul” control and disables bench selection, clearing, combinations,
hints and reset until an authoritative read succeeds. A changed saved pointer instead offers
“Încarcă jocul curent” without sending another mutation to the old round. New-round attempts,
saved-game adoption and unmount invalidate old tickets. A stale completion cannot release a
newer ticket's lock, adopt a different round, clear its pointer or record an old result.

GET supplies complete inventory, counters, private target view and terminal results, but
cannot reproduce the transient `discovered` or `already_tried` combine verdict. Recovery
therefore adopts inventory and uses neutral synchronization feedback, with no invented
empty-pair failure. Normal successful empty responses retain their existing change-one-
ingredient guidance and free duplicate memory. The normal once-per-game score receipt
records a recovered terminal result. An owned 404 returns to setup and conditionally forgets
only its own saved id; a late 404 cannot delete another tab's current game. Exit during
uncertainty preserves the existing saved pointer for ordinary resume.

The server additionally retains one optional `earned_hint` public object containing exactly
`hint`, `hint_kind`, `hint_output` and `message`. These four fields are selected from the
freshly server-authored successful hint response, never from caller input or a full state
snapshot. First hints retain only a non-target output label or generic category direction;
later hints retain one pair of already-owned concepts. This never adds private output ids,
private target ids, recipe maps, routes or an unbounded hint history.

| Event | Retained cue | Hint economy |
|---|---|---|
| Successful paid hint | Replace the single cue; expose it on POST and GET | Existing counter increases once |
| GET/resume or invalid action | Preserve it | No extra hint charge |
| Repeated unordered pair | Preserve it | Existing free repeat; no extra move |
| Accepted new unique pair, productive or empty | Clear it before building the response | Existing move cost; no hint-counter change |
| Winning unique pair | Clear it with that experiment | Existing terminal score and target reveal |
| Reset | Clear it with all progress | Existing moves, experiments and hints reset |
| Defensive no-forward hint | Clear any obsolete cue; do not retain a “none” cue | No additional hint charge |

The browser shows this earned cue in one persistent region, including after GET/resume,
and preselects only a returned earned pair. Reset adoption does not unconditionally rewrite
the saved pointer: the response must belong to the existing owned game. The shared helper,
other game consumers, scoring formula and selector policy remain unchanged.

## Context

Four source-bound actual browser/BFF baseline journeys ran against clean local V89 main.
Each combine, reset, first clue or final winning combine committed successfully, then only
its response was replaced by HTTP 503. Each produced one mutation and zero verifying reads.
The browser omitted the discovery, retained pre-reset progress, lost the charged clue or
failed to show the server-confirmed terminal win. A GET restored ordinary progress but
contained no clue payload, although `hints_used` had increased. Client-only reconciliation
could not recover that paid clue. The one-cue contract makes the existing public information
resumable without repeating a paid action.

The original test attempt had three incorrect toast expectations; the next encountered an
in-progress rubric/sidecar freshness mismatch before game creation. Both attempts remain
archived separately and are not evidence of game recovery. The completed clean-main run
establishes all four baseline behaviors before implementation.

## Consequences

Session TTL remains 7,200 seconds sliding, maximum 1,000 entries per game, with existing
per-session locks. The 64 KiB request bound, 32-concept recipe workspace, at-most-496
unordered experiment memory, 12-reaction browser journal and bounded service caches remain.
One cue replaces itself and is cleared by progress; GET does not advance it or charge it.
Server-authoritative privacy, anonymous production and once-per-game scoring remain.

The saved-pointer guard describes browser ownership, not distributed exactly-once execution.
GET confirms the current session, which may include actions from another browser sharing
that id; it does not claim which request caused a change. Contract tests cover exact cue
retention/clearing and privacy. Actual-BFF desktop/mobile journeys cover uncertainty,
read-only retry, terminal results, reset, cross-tab ownership, unmount and resume.
