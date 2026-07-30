# V45 Lanț pending-pool quality gate

_Reviewed and closed 2026-07-31. This report records the evidence for ADR-0069._

## Scope and release bar

V45 rebuilt exact dossiers for all 107 pending Lanț records against the V44 pack, KG,
and current D1–D5 rubric. The release bar was deliberately quota-free:

1. exact envelope, node, BFS, difficulty-band, and branch-floor validation;
2. a gameplay analyst judging recognition, route meaning, choice, difficulty honesty,
   and discovery arc;
3. an independent inventory verifier checking freshness, duplicate corridors, endpoint
   use, salience, and shelf pressure;
4. conservative synthesis: two promotions are required to ship, either rejection
   rejects, and every other disagreement remains pending only when neither reviewer
   rejects.

The archived V42 judgments were diagnostic history only. Their verifier coverage was
incomplete and every available binding was stale, so none was copied or applied.

## Gate defect and deterministic census

The first fresh run exposed a fail-open workflow defect. `critique_pack.py --strict`
reported no Lanț failures even though the runtime validator rejected most of the pool.
V45 now joins the exact runtime `validate_payload` result into every Lanț review as a
`lant_playability` FAIL. A regression test prevents the dossier gate and runtime from
drifting again.

The corrected full run found:

- all 107 records have a valid envelope, resolvable endpoints, exact BFS par, and the
  correct distance band;
- 91 records are nevertheless unservable: 86 fail both the two-first-hop and two-wide
  shortest-layer floors, while five branch initially and later collapse to width one;
- those 91 records produce 177 deterministic FAIL findings;
- 75 records have exactly one shortest route, and all 75 are in the invalid set;
- 103 endpoint salience warnings affect 69 records;
- only 16 records are structurally eligible for subjective review.

No empty shelf or category quota overrode these findings.

## Independent review of the 16 structural survivors

| Board | Analyst | Verifier | Final | Strict reason |
|---|---|---|---|---|
| `lt_film_tv_100` | reject | keep | reject | Numeric width comes from flat channel/device taxonomy; normal difficulty and discovery are artificial. |
| `lt_gastronomie_212` | reject | reject | reject | Two generic food-category branches and graph-authoring labels, with no discovery arc. |
| `lt_gastronomie_218` | reject | reject | reject | An obvious soup–carrot association is stretched through noisy Jamila, murături, drink, and generic-food routes. |
| `lt_literatura_210` | promote | keep | keep | The school-reading diamond is legible, but the verifier would not ship it beside the near-identical childhood-route family without another comparative pass. |
| `lt_meme_net_050` | reject | reject | reject | Niche Ușor endpoints and platform-taxonomy routes miss the recognition and difficulty bars. |
| `lt_meme_net_054` | reject | reject | reject | Weak start recognition and co-occurrence through comments, memes, and language do not form an inferable chain. |
| `lt_muzica_183` | reject | reject | reject | The target node is the band Vama Veche while one route treats it as the village; the homonym makes the board deceptive. |
| `lt_stiinta_200` | reject | keep | reject | A direct calorifer–căldură idea becomes an arbitrary five-hop path through block costs, water, and generic science. |
| `lt_stiinta_202` | reject | reject | reject | David Popovici reaches fluid mechanics through nationality and unrelated people instead of an inferable swimming arc. |
| `lt_stiinta_215` | reject | reject | reject | `om → corp/ochi → Nas` is a same-taxonomy drill rather than two meaningful routes. |
| `lt_stiinta_216` | keep | keep | keep | `Apă → Ploaie/aer → Nor` is promising, but visible relations such as “două drumuri prin vreme” and “duce la” need semantic rewriting. |
| `lt_stiinta_219` | reject | reject | reject | Dense generic science hubs create numeric branching without coherent player reasoning. |
| `lt_viata_de_roman_211` | keep | keep | keep | The childhood-reading routes are strong, but the current opening menu shows none of the two shortest hops. |
| `lt_viata_de_roman_213` | reject | keep | reject | Excellent width masks a flat same-school shelf and a weak `Ghiozdan → Lecție` discovery arc. |
| `lt_viata_de_roman_214` | reject | reject | reject | A bathroom is routed through house/door to its own room hypernym; obvious fixtures become misleading detours. |
| `lt_viata_de_roman_217` | promote | reject | reject | The analyst liked its furniture arc; the verifier found generic room-to-room co-occurrence. Unanimity correctly blocks release. |

The analyst rejected all 91 structural failures. The verifier marked eight of them as
possible future graph-repair ideas, but a rejection is final under the conservative
synthesis rule. This avoids retaining another large, indefinitely pending repair queue.

## Applied outcome

- **0 promoted:** no board received two independent promotion judgments.
- **104 rejected and removed:** 91 structural failures plus 13 subjective failures or
  rejection disagreements.
- **3 kept pending:** `lt_literatura_210`, `lt_stiinta_216`, and
  `lt_viata_de_roman_211`.

Lanț is now 97 records = 94 approved/selectable + 3 pending. The original-game pack is
724 records = 608 approved + 116 pending, while runtime eligibility stays 447 because
only dormant pending debt was removed.

Rankings and derived metadata were regenerated. The frozen derived `boards` payload is
unchanged at 336 records (183 Intrusul / 153 Perechi), SHA-256
`71a2acefb7e0ec62da32ad2645238d73d5e83375808160c0bd1800febd3a73b6`.
The KG, mobile snapshot, session limits, graph topology, and frontend are unchanged.

The exact machine evidence is `critique.json`, the 107 files under `dossiers/`, and
`lant_verdicts.json`. Rejected Lanț records do not yet have a dedicated import-time
tombstone ledger, so preserving this complete evidence is mandatory; adding a generic
route-rejection ledger is a future workflow hardening task, not a reason to retain weak
runtime stock.
