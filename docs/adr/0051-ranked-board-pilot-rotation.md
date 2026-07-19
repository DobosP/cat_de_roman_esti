# ADR-0051: Rank pilot boards without claiming measured fun

Date: 2026-07-19
Status: accepted

## Decision

Bind a separate version-1 board-ranking artifact to the exact curated pack, knowledge
graph, and critique rubric. Rank every curated record with a deterministic editorial
estimate made from 60% Romanian familiarity and 40% game-specific play quality. Romanian
familiarity is a proxy derived from the graph's Romanian corpus/centrality salience over
the concepts a player must recognize; play quality reuses the critique dossier's bounded
fairness, neighborhood, route, and recipe evidence. Keep `pilot_eligible` independent of
the numeric score: a record is eligible only when it is approved, payload-valid, and has
no deterministic critique `FAIL`.

After the existing game/category/difficulty/repeat filters, prefer eligible boards whenever
that shelf still meets its existing minimum; otherwise retain the approved-content fallback.
Give eligible approved boards one to five integer selection tickets by within-game score
quintile. Seeded play uses weighted integer choice and daily play uses versioned virtual
rendezvous tickets, preserving determinism and leaving lower-ranked eligible content reachable.
Ranks, weights, pack IDs, and eligibility remain server-private.

Treat the initial lobby order—Alchimie, Conexiuni, Cald sau Rece, then Lanțul Cuvintelor—as
a pilot hypothesis. Highlight only Alchimie with `Începe aici`, and omit the empty history
wall before a player's first completed game. Do not enable accounts, public rankings, or
client-authored score uploads for the anonymous pilot.

## Context / why

Uniform selection treated mechanically approved boards as equally suitable for a first
large audience even though the later critique layer already identified deterministic
fairness failures in part of the approved Conexiuni stock. A hard top-N cut was rejected:
small category/difficulty shelves would become empty, lower-ranked boards could never
disprove an inaccurate editorial estimate, and avoid-repeat progression would stall.
Putting scores into `games_pack.json` was rejected because the exact envelope is shared by
submissions and review tooling, and changing it would invalidate existing dossier bindings.

The estimate is deliberately not named a fun score or a measurement of Romanian knowledge.
The graph salience blends Romanian corpus frequency, graph centrality, and structured-source
priors, while the structural component predicts legibility and fairness; neither represents
observed player enjoyment. English analogues focus the first action in different ways:
[Infinite Craft](https://neal.fun/infinite-craft/) begins with a tiny discovery inventory,
[Connections](https://thenewyorktimeshelpcenter.helpjuice.com/360011158491-New-York-Times-Games/28525912587924-Connections)
uses one curated 16-word partition, [Semantle](https://semantle.com/faq/) offers unlimited
semantic probes, and [Wikispeedia](https://dlab.epfl.ch/wikispeedia/play/) presents bounded
missions. Connections and Wikispeedia also report player-derived difficulty or outcomes.

## Consequences

The full inventory has an inspectable, reproducible rank; ranking never changes review
status, and only approved content remains servable. The first pilot sees safer and stronger
boards more often, but same-release daily stability, seed reproducibility, category and
difficulty filters, repeat avoidance, hidden answers, mined fallbacks, two-hour session TTL,
and the 1,000-session cap remain intact.
Custom packs without a matching sidecar retain neutral weight-one selection.

The scores must be described as `estimare editorială pre-playtest`. Recalibration requires
bounded server-authored aggregate outcomes keyed by internal board ID—not public rankings,
client-supplied scores, identities, raw guesses, or free text—and is a separate privacy and
storage decision. Any pack, graph, or rubric change invalidates the artifact until it is
regenerated and reviewed.
