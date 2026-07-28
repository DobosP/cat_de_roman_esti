# ADR-0064: Keep the daily streak device-local and the diploma derived

Date: 2026-07-28
Status: accepted

## Decision

As the narrow exception to ADR-0061's no-persisted-daily-aggregate rule, store one bounded
`_streak` record beside the browser score document. Any valid daily completion, including a
zero-score loss, counts once for its calendar day. The next consecutive day increments the
length, a later gap restarts it at one, an older imported date cannot move it backward, and
the stored length is capped at 20,000. Display the last streak on its completion day and the
following day so it does not appear broken before today's play is possible.

Treat `_streak` as device state, not portable score history. Export omits it; import snapshots
and preserves the pre-import local value, including an explicit zero sentinel; account score
uploads never contain it; clearing local scores clears it. A legacy browser with no valid
record may conservatively reconstruct a run from daily rows already present before import.

When the current browser score document completes all six games for a day, render a diploma
summary and offer a clipboard share string. Store no diploma artifact and make no API,
telemetry, or account write. Because the diploma is derived from ordinary daily score rows,
a player-controlled history import can intentionally reconstruct it on another browser; this
is not automatic account continuity.

## Context / why

The local six-game circuit showed completion but offered no small reason to return or moment
of closure. A server streak, attendance event, or analytics stream was rejected: it would
create a new identity/retention decision for a motivational feature. Reconstructing a streak
from newly imported rows was also rejected because it would make a supposedly device-local
habit change during history restore.

## Consequences

The browser document gains one reserved, validated two-field record that is excluded from
the game-key cap. Malformed storage remains non-fatal. Same-day writes are idempotent,
out-of-order daily history cannot inflate the streak, and all date arithmetic uses validated
calendar keys. ADR-0061's browser-as-source-of-truth, upload-only account backup, 6,000-point
circuit cap, and no automatic download/merge remain unchanged.
