# ADR-0052: Add two ranked games from strict derived catalogs

Date: 2026-07-19
Status: accepted

## Decision

Add exactly two mobile-first games without widening the reviewed knowledge space:
**Intrusul**, where a player taps the one word outside a coherent three-word group, and
**Perechi**, where a player finds one semantic pair from each of four hidden groups. Build
both catalogs offline from the 123 V37 pilot-eligible Conexiuni boards. Never enumerate
candidates during a request and never fall back to mined or unreviewed derived content.

For Intrusul, require the three members and intruder to share a node type, at least two of
the three member links to have strength 0.60 or greater, and the intruder to have no
non-distractor link to any member. For Perechi, require every intended pair link to have
strength 0.60 or greater and every unintended on-board pair link to remain below 0.60.
Keep at most three diversity-first variants from each source board. Bind the resulting
catalog to the exact pack, KG, critique rubric, and V37 ranking artifact, and pin its own
normalized digest in the runtime loader.

Rank derived boards separately from their source. The standard score is 60% visible-word
familiarity plus 40% derived mechanic clarity; the starter score is 75% familiarity plus
25% clarity and requires stronger links and a higher weakest-word salience. Select a source
first and then a candidate so prolific sources do not dominate. Convert fixed score bands
to integer tickets so equal scores always receive equal weight. Assign tied scores the same
competition rank (`1, 1, 3`); ranks are an audit field, not a public leaderboard. Keep all
source IDs, catalog IDs, scores, ranks, gates, and weights server-private. Fail closed when
the bundled pack, KG, critique rubric, V37 ranking artifact, or generated catalog drifts,
and when a runtime pack, KG, or V37 ranking override is active. Do not change V37 selection
or any existing daily assignment.

Use only single taps: no dragging and no free-text answer. Give Intrusul three distinct
wrong taps and one label hint; give Perechi four matches, six distinct mistakes, and one
earned pair hint after two mistakes. Repeated wrong tiles or unordered pairs are free.
Score an Intrusul win as `max(100, 1000 - 200 × mistakes - 150 × hint)` and a Perechi
win as `max(100, 1000 - 100 × mistakes - 150 × hint)`; a loss scores zero. Preserve the
shared 7,200-second TTL, 1,000-session cap, atomic mutation, terminal answer gate, and
server-authored scoring. Carry at most four private source IDs through a live
previous-game reference for anonymous repeat avoidance.

When the separate frontend integration lands, order the six-game lobby Alchimie, Intrusul,
Perechi, Conexiuni, Cald sau Rece, then Lanț; only Alchimie keeps `Începe aici`. Keep the
new boards tap-first with short feedback and comfortably sized controls.

## Context / why

The four original mechanics leave a gap between a first tap and their larger search spaces.
The reviewed Conexiuni stock already contains authored labels and unique partitions, but
using every possible 3+1 or pair combination would recreate ambiguity and heavily repeat a
few prolific boards. The strict graph gates produce a finite launch inventory while the
per-source cap prevents candidate count from becoming exposure probability.

Unfiltered odd-one-out mining was rejected because a missing graph edge is not proof that a
word cannot fit a human predicate. Free-text clue guessing was rejected because aliases,
inflection, and spelling would reintroduce the input friction V34–V37 reduced. Drag matching
was rejected because two taps express the same action more directly; WCAG 2.2 also requires
a single-pointer alternative when dragging is used. Flat candidate selection, ordinal
quintiles that split tied scores, and changing the four existing daily schedules were
rejected.

The interaction model is a product inference, not evidence of measured enjoyment. Wordwall's
[matching-pairs template](https://wordwall.net/about/template/pairs) uses two tile taps, while
the W3C guidance for [dragging movements](https://www.w3.org/WAI/WCAG22/Understanding/dragging-movements)
and [target size](https://www.w3.org/WAI/WCAG22/Understanding/target-size-minimum) supports a
tap-first interface with comfortably sized controls.

## Consequences

The committed launch catalog contains 183 Intrusul boards from 66 sources and 153 Perechi
boards from 51 sources. The stricter starter shelves contain 24 and 26 boards respectively.
Every served board is reproducible, source-balanced, critique-gated, and inspectable offline;
runtime pack, KG, or V37-ranking overrides fail closed until a matching derived catalog is
designed, and bound-artifact drift is rejected.

The two modes remain editorial pre-playtest hypotheses. Their rankings must not be displayed
as fun or Romanian-knowledge scores. Calibration still requires a separate privacy decision
for bounded server-authored aggregate starts, outcomes, hints, and action counts. A pack, KG,
rubric, V37-ranking, formula, or generated-catalog change requires explicit regeneration,
review, and a new release.
