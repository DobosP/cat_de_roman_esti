# V88 six-game impact review

Valid until: the captured backend artifacts or runtime sources change — then treat as history.

Verified 2026-09-08 against V87 baseline commit
`2878417ed43aaf790badfa09297ea122121b9449` and the frozen V88 backend after all
three promotions. The final capture made **11,233 fresh first-guess API requests**
in 82.181 seconds: **47 inputs × 239 old approved Contexto records**, representing
236 distinct targets. No baseline was recomputed. This is deterministic impact
evidence, not a human playtest or the independent review of newly promoted rounds.

## Existing stock and guidance

| Measure | V87 baseline | Frozen V88 |
|---|---:|---:|
| Source pack records | 655 | 658; all 655 old records exact |
| Approved / pending pack records | 647 / 8 | 650 / 8 |
| Conexiuni eligible | 74 | 76 |
| Contexto eligible | 235 | 235 |
| Lanț eligible | 97 | 97 |
| Alchimie eligible | 79 | 80 |
| Old Alchimie projections and validation profiles | 82 | 82 exact |
| Old Lanț distance and branch profiles | 100 | 100 exact |
| Intrusul / Perechi complete board rows | 183 / 153 | 183 / 153 exact |
| Intrusul / Perechi preferred pools | 144 / 113 | 144 / 113 exact |

The three additions are `al_gastronomie_107`, `cx_viata_de_roman_362` and
`cx_viata_de_roman_363`. Combined curated eligibility grows **485→488**. No old
eligible, preferred or starter entry is lost. Both derived games retain their
complete board rows, payloads and selection profiles; changed artifact source
bindings do not constitute new boards. All old Alchimie targets remain reachable
with valid projections and unchanged recipe, route, result, concept and par bounds.
All old Contexto and Lanț validation profiles remain valid.

One initial Lanț menu changes: `lt_stiinta_216` shows **Găleată in place of
Saramură** within its six-choice limit. Its shortest options, aer and Ploaie,
remain shown. Across all 100 old records, all **206 shown shortest first hops**
remain, with no menu-bound failure. This is a visible nonshortest choice change;
the report does not claim all menus are exact. See [the complete menu comparison](lant-guidance.json).

All **33 added directed links** produce an actual typed one-move Lanț API win.
Every one of these routes required a node absent from the baseline. These probes
cover the added directions; the removed fermented-cream link is covered separately
by the graph and content tests. This impact capture does not claim another probe
of that removed direction or public selection journeys for the three additions.

## Feedback gains and costs

The 11,233-observation comparison contains **8,540 changed and 2,693 exact**
response records. It includes **1,434 newly accepted observations** across six
input columns, **478 native identity replacements** for Mătură and Taburet, and
**zero lost accepted inputs**. Six columns represent five newly accepted concepts:
the qualified cream label and its accepted short form resolve to the same identity.
Cariocă and bare `smântână dulce` remain unaccepted controls in all 239 records.

Among observations accepted in both versions, **396 temperatures** and **467
distances** change: **306 cooler, 90 warmer**. Another **6,559 changed observations**
retain both temperature and distance. Counts include rank and closeness movement,
vocabulary acceptance and identity changes; they are not counts of proven quality
improvements. The categories overlap where an observation changes several fields.

| Guess → hidden target | V87 | Frozen V88 |
|---|---|---|
| Brioșă → Pâine | 424, four hops, cold | 2, feedback distance one, hot |
| Chec → Pâine | 193, three hops, lukewarm | 194, three hops, lukewarm |
| Brioșă → Zacuscă | 206, three hops, lukewarm | 208, three hops, lukewarm |
| Chec → Zacuscă | 531, four hops, cold | 532, four hops, cold |
| Smântână / smântână fermentată → Frișcă | 2, one hop, hot | 34, three hops, warm |
| smântână pentru frișcă → Frișcă | unaccepted | 2, one hop, hot |
| smântână pentru frișcă → Tort Diplomat | unaccepted | 2, one hop, hot |
| Prăjitură → Frișcă | 53, three hops, warm | 181, four hops, lukewarm |
| Tort Diplomat → Frișcă | 142, four hops, lukewarm | 345, five hops, cold |
| Cremșnit → Frișcă | 228, four hops, lukewarm | 504, five hops, cold |
| Pișcot → Frișcă | 390, five hops, cold | 944, six hops, very cold |
| Brioșă → Pișcot | 227, five hops, lukewarm | 239, five hops, cold |

Ranks and feedback distances above are actual first-guess response fields. The
Brioșă→Pâine result is the exact feedback repair, not a new graph edge, inverse
edge or winning alias. Its native Brioșă identity remains nonwinning. The full
qualified label `Smântână dulce pentru frișcă` matches the accepted short cream
form in the table. The retired fermented-cream edge no longer promises that sour
cream whips into Frișcă, but indirect feedback still leaves that input warm. The
reverse dessert cues toward Frișcă become weaker; this is a remaining semantic
cost of the factual graph correction, not silently classified as an improvement.

Of the **306 cooler observations**, **290** come from the two retired projections:
184 Taburet observations and 106 Mătură observations. Native ownership stops
Taburet from borrowing Casa and Mătură from borrowing Aspirator, but also weakens
some familiar contextual cues. For example, Taburet→Viața la bloc falls from
39/warm to 678/cold, and Taburet→Vecinul cu bormașina from 59/warm to 1096/very
cold. Of **18 previously warm/hot observations that cool**, 12 are Taburet
identity replacements and six target Frișcă. All 18 remain included in
[the full 306-row cooler-cue file](cooler-old-target-cues.json).

There are also incidental warmer paths: Taburet→Carla's Dreams moves from
1393/very cold to 190/lukewarm. A warmer result alone is not evidence that an
association is more intuitive. [All 90 warmer observations](warmer-old-target-cues.json)
remain available beside the cooler results. No general semantic-ranking quality
claim or new Contexto target approval follows from these counts.

Retained controls remain intact: Făină, Unt and Zahăr→Biscuit stay rank 4/hot;
Prăjitură→Cremșnit stays rank 2/hot; projected tort→Cremșnit stays cold (255→257);
Frișcă and projected tort→Tort Diplomat stay rank 2/hot. The table and controls
are backed by [exact before/after responses](core-associations.json) and
[the aggregate comparison](summary.json).

## Evidence preservation and reproduction

[capture-receipt.json](capture-receipt.json) binds every input, capture, artifact,
runtime source, report and reproduction script. All five complete matrices survive
as lossless gzip archives under `raw/`, with timestamp zero and both decoded and
archive byte hashes. The original logs, full comparison, comparison stdout and
exact audited baseline pack are archived too. The final capture's nine source
hashes were checked again during archival, and the baseline's nine hashes match
the explicit baseline commit. Supplemental fingerprints cover 46 tracked package
Python files, including the derived-catalog loader.

The original baseline history is retained without replacement:

| Capture | Input columns | Fresh requests | Reused observations |
|---|---:|---:|---:|
| `baseline.json` | 38 | 9,082 | 0 |
| `baseline-expanded.json` | 40 | 478 | 9,082 |
| `baseline-final-inputs.json` | 41 | 239 | 9,560 |
| `baseline-reviewed.json` | 47 | 1,434 | 9,799 |
| `final.json` | 47 | 11,233 | 0 |

Every reused observation and structural profile was checked against its archived
predecessor, with exact source and audited-pack equality. Earlier input files and
capture logs remain distinct. Initial independent judgments and author proposals
elsewhere in the wave were not edited by this lane.

To reproduce, copy [capture.py.txt](capture.py.txt) and [compare.py.txt](compare.py.txt)
into task scratch as Python files. Use the named shared Python interpreter with
`PYTHONPATH=.` from the chosen checkout. The final capture invocation is
`capture.py --root CHECKOUT --baseline-pack BASELINE_PACK.json --inputs
reviewed-inputs.json --out FINAL.json`; extract `raw/baseline-pack.json.gz` for
the identical audit scope. Then run `compare.py BASELINE_REVIEWED.json FINAL.json
COMPARISON.json`. The optional baseline-expansion mode rejects source or scope
mismatches. The analysis and archival scripts are retained beside the capture scripts.

This lane ran no full backend, accounts, frontend or browser suite. New-round
judgments, graph inverses, public journeys and integration gates are reported by
their owning lanes. Human Romanian-player sessions and production readiness are
outside these measurements.
