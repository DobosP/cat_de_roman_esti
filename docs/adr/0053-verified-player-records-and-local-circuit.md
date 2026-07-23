# ADR-0053: Separate verified player records from the local daily circuit

Date: 2026-07-23
Status: accepted

## Decision

Keep anonymous play and accounts-off deployment as the default. When accounts are enabled,
publish only a server-authored best score for one selected game at a time. Accept exactly the
six public game keys and retain at most one `VerifiedBest` row per user and game, with an
integer score from 0 through 1,000. Update that row only from the game's terminal server
action and never from imported or browser-authored score history.

Require the consent version currently in force, no parental-consent hold, an explicitly
chosen nonblank nickname, and a separate `show_on_ranking` opt-in before a player appears.
Default and migrate that preference to private. Never derive a public label from Google name
or email. Use competition ranks for ties (`1, 1, 3`), identify the requester's row explicitly,
and return one bounded personal row when it falls outside the requested top list.

Keep synced `ScoreEntry` rows private and cap them at the newest 500 arrivals per user.
Validate their exact game, 0–1,000 score, timestamp envelope, daily date, difficulty,
category, and control-character-free puzzle key. Recheck current consent while holding the
user's profile row for both sync and verified-record writes. Keep `PlayedPuzzle` repeat
avoidance behind the same current-consent gate.

Build the six-game daily circuit only from the browser's existing local score document.
Count a retained zero-score daily completion, take the best score for each game, clamp every
contribution to 0–1,000, and cap the displayed total at 6,000. Do not persist or upload a
daily aggregate, board identity, start, action, hint, outcome, or telemetry event.

## Context / why

The previous ranking endpoint aggregated client-supplied history, so an imported score could
become a public result. It also mixed games with incomparable mechanics and let old consent
state remain effective after a policy-version change. A chosen public pseudonym and a
server-scored terminal action create a smaller, explainable trust boundary.

A cross-game public total was rejected because six mechanics do not measure one common
Romanian-knowledge scale. Google-derived handles and ranking-on defaults were rejected
because public participation must be deliberate. Public daily completion, action telemetry,
and board-key persistence were rejected until a separate purpose, retention period, and
privacy review exist. The local circuit supplies the useful habit cue without creating that
dataset.

## Consequences

Public ranking rows are bounded to six per consenting opted-in player and contain no board,
answer, daily, category, difficulty, action, or private editorial-rank fields. Personal
history can still sync across devices but cannot influence public standings. Revoked or stale
consent immediately removes visibility and blocks further account-linked progress writes.

Accounts mode still requires the compliance go-live checklist and remains disabled in the
anonymous release. The circuit is device-local, so another browser will correctly show
different daily progress. Any future all-game rating, telemetry, child-account ranking, or
public daily streak requires a new decision and privacy review.
