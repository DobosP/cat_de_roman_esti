# ADR-0060: Keep progress device-local and account history upload-only

Date: 2026-07-24
Status: accepted

## Decision

Keep the browser score document as the source of truth for personal history, best scores,
derived-game mastery, and the six-game daily circuit. Local export/import remains the only
player-controlled way to move that document. Account mode must not promise automatic
cross-device continuity.

When accounts are enabled, allow the frontend to upload retained completed-score rows only
after current consent and with no parental-consent hold. Treat those `ScoreEntry` rows as a
private, best-effort backup: validate their exact game, 0–1,000 score, timestamp envelope,
optional daily date, difficulty, category, and control-character-free puzzle key; deduplicate
them by user, game, timestamp, and puzzle key; and retain at most the newest 500 server
arrivals per user. The authenticated read endpoint remains available for account access and
data-rights work, but the current frontend does not download, restore, or merge its response
into the browser score document.

A Google/allauth user and `Profile` can exist before valid self-consent. An under-threshold
declaration creates a sticky parental-consent hold: until a verified parental flow exists,
it blocks `ScoreEntry`, `PlayedPuzzle`, and `VerifiedBest` writes plus ranking visibility.

Keep repeat avoidance separate. Under current consent, `PlayedPuzzle` stores the game key,
opaque curated pack ID, and server-authored completion timestamp. It never derives from
`ScoreEntry` and never stores a mined board or solution.

Keep public records separate. Accept exactly the six public game keys and at most one
`VerifiedBest` row per user and game, with an integer score from 0 through 1,000. Update it
only from that game's terminal server action, never from browser-authored or imported score
history. Public visibility requires current consent, no parental-consent hold, an explicitly
chosen nonblank nickname, and a separate `show_on_ranking` opt-in. Never derive a public
label from Google identity. Use competition ranks for ties, mark the requester's row
explicitly, and return one bounded personal row when it falls outside the requested top
list.

Build the daily circuit only from the browser score document. Count a retained zero-score
daily completion, take the best score per game, clamp each contribution to 0–1,000, and cap
the displayed total at 6,000. Do not upload or persist a daily aggregate, active progress,
mastery state, action trail, hint, or telemetry event.

## Context / why

ADR-0053 correctly separated server-verified public records from browser-authored history
and made the daily circuit device-local, but its consequence claimed that personal history
could sync across devices. The implemented frontend only posts recent completed-score rows.
It never calls the account score read endpoint and cannot reconstruct local bests, mastery,
imports, or the daily circuit from those rows.

Automatically merging server rows was rejected. The browser store is not namespaced by
account, so a shared browser or account switch could mix identities. A merge could also
change device-local daily completion or derived starter progression without a defined
conflict rule. Calling the existing upload a sync was rejected because that would promise a
recovery path the product does not provide.

## Consequences

Losing or changing a browser can lose its displayed progress even when private score rows
exist on the account. Account deletion immediately cascades through `Profile`,
`ConsentRecord`, `ScoreEntry`, `PlayedPuzzle`, and `VerifiedBest`; it does not clear another
browser's localStorage. The current model does not retain consent evidence for three years
after deletion. Such evidentiary retention remains an unimplemented legal and data-model
decision. Browser-authored rows remain unable to influence public standings.

Accounts mode remains behind its compliance go-live checklist. A future automatic download
or merge requires a new decision covering account-namespaced local storage, account
switching, conflict and deletion semantics, mastery and daily isolation, privacy copy, and
deterministic tests.

Anonymous play, hidden-answer boundaries, score rules, deterministic board selection, the
7,200-second sliding session TTL, and the 1,000-session per-game cap do not change.
