# V85 independent six-game impact review

Valid until: the captured graph, runtime source or final pack artifacts change — then treat as history.

Verified 2026-09-07 against local main `39b64cb` and the final V85 candidate.
One source-bound baseline set and one final candidate set cover all six games.
The expanded baseline reused the exact unchanged recipe/route profiles when adding
ingredient words; it did not rebuild the 82 Alchimie projections a second time.

## Coverage and preserved playability

Each checkout received 5,376 first guesses: 24 specified words across all 224 old
approved Contexto records. All 82 Alchimie recipe projections, 98 Lanț route profiles,
638 old source records and 336 derived boards were compared. This is deliberate
input coverage, not a claim to exhaust every possible player spelling or association.

- All 82 Alchimie projections remain exact, reachable, valid and within existing bounds.
- All 98 Lanț route profiles remain exact and valid.
- All old curated eligible, derived preferred and starter pools remain available.
- Four Contexto records and one Lanț record are added; the other game stocks do not grow.
- The sole changed old source record is `cx_gastronomie_171`, containing the reviewed
  two label corrections. The sole changed frozen payload is Intrusul board
  `vi_1535ff1ac283061d41a1`, containing its reviewed label correction. Perechi is exact.
- All 45 oriented journeys supplied by the 40 new links now win by one typed move.
  The separate retained-endpoint Mucenici label replacement is not counted as a new link.

## Measured feedback changes

| Guess → target | V84 | V85 |
|---|---|---|
| Scorțișoară → Pâine | 4, hot | 483, cold |
| Scorțișoară → Sarmale | 8, hot | 313, cold |
| Scorțișoară → Plăcintă cu mere | 22, warm | 3, hot |
| Unt → Plăcintă cu mere | 506, cold | 3, hot |
| Cacao → Salam de biscuiți | 62, warm | 3, hot |
| Cuptor de bucătărie → Salam de biscuiți | 36, warm | 42, warm |
| Cuptor de bucătărie → Plăcintă cu mere | 78, lukewarm | 94, lukewarm |

Cinnamon and cocoa retain their typed labels while moving from synthetic identities
to the reviewed native nodes. Cocoa now outranks the oven for the biscuit dessert;
the oven response itself remains too warm. Its apple-pie response is still weaker
than expected. Butter also changes unrelated positions through the new graph route;
for example, Telemea moves from 823/cold to 114/lukewarm. These shifts are disclosed.

Across the full input matrix, 3,867 observations differ. Many differences are native
identity changes, newly accepted words, extra reachable nodes or rank positions.
They are not 3,867 proven quality repairs. Previously accepted inputs remain accepted;
bare `cuptor` and `praf de copt` remain unsupported. The old source/alias boundaries
are verified separately by the compatibility tests and graph review.

## Evidence and limits

`summary.json` contains all pool deltas and per-word counts. `core-associations.json`
contains the selected actual response pairs. `capture-receipt.json` binds the source
files and raw capture hashes; the exact reproducer and inputs are archived alongside.
Raw observation matrices remain in task scratch. New target judgments and their
private clue/resume/win journeys are in the independent verifier review, separate
from this comparison against old approved records. No human playtest or production
observation is implied by these deterministic API checks.

## Broad compatibility before full integration

The 58-module V24–V84 run executed 599 cases: 592 passed and seven old Clătite
rank-position expectations failed. The two new flavor inputs changed rank positions,
while the asserted identities, distances and temperatures stayed the same.

Exact V83 and V84 numerical snapshots remain tested on reconstructed historical
graphs. Current opener ranks are now manually authored once in the immutable shared
snapshot. Both affected modules, complete V84 artifact reconstruction, and current/
historical projection coverage then passed together: **48 checks in 15.827 seconds**,
no failures, errors or skips. Ruff and whitespace checks passed. The initial failure
receipt is retained alongside the successful focused follow-up; this is not presented
as a clean first run or a replacement for root's full backend matrix.
