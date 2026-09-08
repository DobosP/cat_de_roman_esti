# V88 — familiar choices across games

Valid until: any final source, artifact or validation binding changes — then treat as history.

Started 2026-09-08 from local main `2878417ed43aaf790badfa09297ea122121b9449`,
which includes landed V87 `fa8cffd`. Active branch: `feat/v88-cross-game-quality`.
Implementation, content promotion, independent review and full integration are GREEN.
V88 is ready for local landing. No push or deployment.
The authorized local loop follows [ADR-0127](../../adr/0127-recurring-local-version-loop.md).

## Delivered player outcomes

Lanț now recovers committed moves, undo and hints whose replies were lost. It checks
actual server state once and retains a read-only retry if verification fails. Earned
hint content survives that check and resume without consuming another stage. The shared
action owner also retains V87 Contexto behavior. A new portable Alchimie review path binds
both independent judges to the exact sparse recipe book before any approval is applied.

The content batch introduces useful everyday tools and separates sweet whipping cream
from the existing fermented smântână owner. It adds one multi-step Alchimie round and two
Conexiuni boards. A closed Brioșă→Pâine cue fixes one recorded cold bread-family response.

| Metric | V88 change | Final inventory |
|---|---|---|
| Native concepts | +7 | 2,413 |
| Directed graph links | +33, one unsupported old link removed; net 32 | 9,442 |
| Accepted forms | +28: 25 grammatical, three qualified | 8,631 |
| Reviewed lexical equivalents | +0 | No synonym claim |
| Projected inputs | Retire Mătură and Taburet only | 465 across 26 domains |
| Exact native feedback pairs | +1 Brioșă→Pâine | 10 |
| Alchimie rounds | +1 authored/promoted/eligible | 83 total, 80 approved/eligible |
| Conexiuni boards | +2 authored/promoted/eligible | 234 total/approved, 76 eligible |
| Contexto / Lanț rounds | +0 | 235 / 97 eligible |
| Intrusul / Perechi boards | +0; all full rows exact | 183 / 153; 144 / 113 preferred |
| Legacy puzzles | +0; all exact | 180 |

New concepts are Compas, Echer, Raportor, Mătură, Taburet, Cratiță and qualified
Smântână dulce pentru frișcă. Every new node meets the actual four-distinct-neighbor/
two-same-category preflight floor through reviewed uses. All old owners and forms stay
exact; de8676 is the sole removed edge. Bare smântână and its fermented aliases keep
their existing owner. Bare smântână dulce remains an unresolved control; the new cream
forms explicitly qualify whipping use. No new hidden Contexto target is approved.

## Playable content and deliberate deferrals

- **Alchimie `al_gastronomie_107`: Cremșnit, normal.** Five useful seeds lead to a
  three-action target. The served book has four openings, five recipe pairs, eight
  concepts and three complete routes. Flour+water→Aluat and milk+vanilla→Cremă de vanilie
  are the clearest starts. Sugar-based cream shortcuts are an explicit simplification.
- **Conexiuni `cx_viata_de_roman_362`: everyday household/school, easy.** Geometry-set
  instruments, floor-cleaning tools, connected plumbing fixtures and garden tools.
- **Conexiuni `cx_viata_de_roman_363`: everyday household, easy.** Domestic electrical
  components, manual workshop tools, seating furniture and cooking vessels.

The two Cx boards are introductory functional classifications. Exact dossier critique
shows no lint, contested-tile, raw-fairness or strong cross-group finding. Independent
review walks plausible broom/rake/plumbing and electrical/manual-tool cross-fits.
Novelty checks include all 234 source boards and 122 validated tombstones: maximum old
board overlap is one tile for 362 and zero for 363; maximum projected member use is one.
All three candidates received separate bound analyst/verifier promotion judgments.

The initial writing/bed groups reused three members of a rejected board and were replaced.
The original Diplomat recipe misused fermented smântână as whipping cream. A new correct
cream owner and its true direct Diplomat ingredient link exposed a one-pair answer;
alternatives contained weak openings or unused seeds, so that round remains held.
No missing link was withheld to manufacture a desired par. Pâine, Ciocolată, Înghețată
and several Lanț ideas were also held after actual sparse/route screens. Three strong
rounds across two games survived the planning aim of four to eight; quantity did not
weaken the rubric. Original proposals, judgments and failures remain archived.

## Reliability and review-tool refactors

[Lanț evidence](lant-action/README.md) reproduces a lost win with no client result/score
and a lost hint that advanced to the next stage on retry. One synchronous owner now gates
move/undo/hint and the single authoritative GET. Failed reads pause mutations and keep a
visible retry. Another tab's pointer and unmounted/older callbacks cannot displace a new
game. Recovery replaces an uncertain transient verdict with neutral synchronization text.

The server retains one optional earned-hint payload under existing locks and clears it
on actual position changes. Replacement-only writes keep returned snapshots stable.
The three-stage hint scalar, 7,200-second TTL, 1,000 sessions/game and request/history
bounds remain. Existing terminal effects record confirmed wins once. The helper's
Contexto adaptation is identifier-only; its complete browser recovery suite still passes.

[Portable Alchimie review](TOOLING_REVIEW.md) requires the exact audit file and its raw
SHA-256 on every analyst/verifier item. Existing source, batch, dossier and projection
reconstruction checks execute in private staging before files are copied. Alchimie stays
in a separate sorted exact batch; mixed-game audit scope, missing/stale/tampered evidence
and reused reviewer identity fail closed. The applier and recipe runtime were unchanged.

## Graph and feedback impact

[Complete impact review](impact/IMPACT_REVIEW.md) compares 11,233 fresh first guesses over
239 old approved Contexto records (236 distinct targets) and 47 inputs. All 655 old pack
records, 82 Alchimie books/profiles, 100 Lanț route profiles and 336 derived rows remain
exact. No old eligible/preferred/starter stock is lost. One nonshortest Lanț suggestion
changes Saramură→Găleată; all 206 old shown shortest hops remain.

The Făraș→Mătură→Podea bridge deliberately opens exactly six formerly isolated cleaning
nodes. Historical V87 still has the original cut; removing that single reviewed bridge
from V88 restores it. Other beginner meshes and all 71 scorer mappings remain unchanged.
This does not claim that every old-to-old graph distance is preserved (ADR-0131).

The isolated bread repair changes only Brioșă→Pâine, from 424/cold to 2/hot/nonwinning;
238 other approved-record observations stay exact on unchanged graph bytes. Native
identity, repeats, private answers and exact wins remain. Dictionary brioche and modern
muffin meanings coexist: this is a generous editorial family cue, not a synonym or
unconditional graph is-a assertion. Only Mătură/Taburet projections retire; Pămătuf
replaces one audit example on the same anchor and has no numeric role.

The complete graph comparison has 8,540 changed and 2,693 exact observations, including
1,434 newly accepted observations, 478 native identity replacements and zero lost
accepted inputs. Those are not 8,540 improvements. Of 306 cooler responses, 290 follow
the two projection retirements. Smântână→Frișcă remains warm at 34; qualified whipping
cream is hot at 2. Reverse pastries weaken: Tort Diplomat→Frișcă 345/cold,
Cremșnit→Frișcă 504/cold and Pișcot→Frișcă 944/very cold. Some household contextual cues
also cool. These are accepted, explicit costs and priority follow-ups in the
[supplemental review](SUPPLEMENTAL_REVIEW.md), not hidden successes.

## Verification and retained failures

- Exact final graph review covers 7 concepts/28 forms/33 additions/one removal. Actual
  preflight covers 324 declared beginner entries (322 eligible) and 33 added links.
- Three complete promotion dossiers have zero FAIL/WARN; the actual Alchimie projection
  audit has no live E2 failure. All three public selection/solve journeys pass.
- **59 new graph/history/public tests, eight bread tests and 80 targeted Lanț/session
  checks pass.** Tooling: 45 focused and 102 existing critique checks pass.
- **193 native frontend and 188 desktop/mobile browser cases pass**, first full run,
  no retries. Lint/typecheck/build/bundle pass at 118.92/120 KiB. Full backend: **1,508 passed on each Python 3.12.3/3.14.6**, plus **53 accounts
  tests each**. Initial runs each passed 1,501 with seven failures. A later Python 3.12
  attempt ended with signal 143 before completion; the unchanged complete rerun passed.
- The seven failures were stale aggregates/live inventories and an older topology
  boundary. Current checks use live pins, retain exact historical fingerprints and
  require the specific six-node opening. All seven remediation checks pass; no game
  source, content, sparse bound or performance threshold was changed to satisfy them.
- Other preserved development failures include duplicate-group debt, graph reciprocal/
  neighbor-floor mistakes, the fermented-cream candidate, compact-invalid-response
  assumptions and three JSON-indent assertions. Root also started one import too early;
  the graph guard restored all five transaction files, verified byte-exact before a
  successful sequential graph apply/import. One malformed CLI ID argument was corrected.
- Seed38 changes Alchimie to Liga Campionilor la handbal and Contexto reachability
  2,330→2,343. The other four initial payloads remain exact. Root inspected recovered
  hint/retry mobile screens and the settled desktop win; real devices remain untested.

Both validators, the strict pending gate, Ruff, documentation and whitespace checks pass.
[Actual verification receipts](verification.json) retain all 16 final green commands and
complete lossless logs, separate initial failures and the incomplete interrupted attempt.
[The review manifest](review-manifest.json) binds the exact changed files and removed assets.

## Evidence map

- [Graph review](GRAPH_REVIEW.md), [author screens](author-screening/README.md),
  [raw candidates](author-candidates/), exact `alchimie-dossiers/` and `conexiuni-dossiers/`,
  separate analyst/verifier JSON files and tool-built `alchimie-verdicts/` / `conexiuni-verdicts/`.
- [Content delta](content-delta.json), [exact artifact inverse](artifact-delta.json),
  [content checks](content-checks/verification.json),
  [seven-failure remediation](content-checks/diagnostic-remediation.json).
- [Bread review](bread-feedback/INDEPENDENT_REVIEW.md),
  [isolated effect](bread-feedback/isolated-impact.json),
  [projection retirement](projection-retirement-review.json),
  [Lanț implementation review](LANT_REVIEW.md), [tooling review](TOOLING_REVIEW.md).
- [Impact captures and lossless archives](impact/capture-receipt.json),
  [semantic/topology decision review](SUPPLEMENTAL_REVIEW.md).
- Decisions: ADR-0128 through ADR-0131 in [the ADR index](../../adr/README.md).

Current state is [STATUS](../../STATUS.md). Human Romanian-player sessions, real-device
acceptance, public contact/operator verification and an authorized rollout remain in
[BETA_CANDIDATE](../../BETA_CANDIDATE.md). This local version is not a production release.
