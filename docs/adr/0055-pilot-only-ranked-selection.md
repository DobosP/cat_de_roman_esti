# ADR-0055: Serve only critique-clean boards from a ranked bundled pack

Date: 2026-07-24
Status: accepted; category-daily floor superseded-by ADR-0063

## Decision

Treat `pilot_eligible` as a hard runtime boundary whenever a digest-validated board-ranking
sidecar is active. Apply game, category, and difficulty filters inside that eligible stock.
For seeded play, honor finished-board exclusions while an unseen eligible board remains; once
that filtered eligible shelf is exhausted, repeat an eligible board instead of widening to a
non-eligible approved board. Keep integer-ticket weighting and deterministic seeded choice.

For daily play, count only eligible boards toward the existing minimum of eight for an
unscoped shelf and one for an explicit category. Return no curated pick when the eligible
shelf is absent or below that floor, leaving each game's existing deterministic mined
fallback or themed-unavailable response in control. Preserve the historical selector for a
custom pack or graph without a digest-matching sidecar.

## Context / why

ADR-0051 used eligibility as a preference so small shelves stayed available. The V40 audit
showed that this fallback was unsafe for a larger pilot: all 86 approved non-eligible
Conexiuni boards carry deterministic strict critique failures, while all 486 eligible
original-game boards carry none. Four easy category shelves exposed only failed boards
immediately, and another 28 mixed shelves switched to them after eligible repeat history was
exhausted.

Keeping known failures reachable was rejected because a larger pilot needs a clear reviewed
content boundary. Returning unavailable after every exhausted signed-in shelf was also
rejected because a safe reviewed repeat is preferable to either a known-bad board or an
artificially dead game.

## Consequences

The ranked bundled runtime serves only the 486 critique-clean original-game boards. A player
may see a safe repeat after finishing every eligible board in an exact filtered shelf.
Conexiuni keeps its existing 503 for the four explicit easy shelves with no eligible content;
unscoped and mineable games retain their existing deterministic fallback behavior.

Daily hashes, hidden answers, score rules, the two-hour session TTL, and the 1,000-session cap
do not change. The 336 derived boards remain governed by ADR-0054 and their already
pilot-clean source catalog. Adding or restoring bundled content requires clearing the
deterministic critique gate and regenerating the digest-bound ranking sidecar.
