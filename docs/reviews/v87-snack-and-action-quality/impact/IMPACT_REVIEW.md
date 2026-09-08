# V87 independent six-game impact and history review

Valid until: the captured backend artifacts or runtime sources change — then treat as history.

Verified 2026-09-08 against committed V86 main `daae025b19517c18cba2f46c6b11ea4991d9a19c`
and the final V87 backend. Each comparable matrix has **9,087 first-guess observations**:
39 inputs over 233 old approved Contexto records, representing 230 distinct targets.
The expanded baseline reused 8,388 observations only after checking exact source and
audit-scope equality, then made 699 extra requests. The final candidate was captured
once, making all 9,087 requests after graph, scoring, promotions and sidecars froze.

## Preserved playable stock

| Measure | V86 baseline | Final V87 |
|---|---:|---:|
| Source pack records | 649 | 655 |
| Approved Contexto records | 233 | 239 |
| Eligible Contexto records | 229 | 235 |
| Approved/eligible Lanț records | 97 | 97 |
| Existing Alchimie projections | 82 | 82 exact |
| Existing Lanț distance/branch profiles | 100 | 100 exact |
| Intrusul/Perechi complete board rows | 336 | 336 exact |

All 649 old source records remain exact. No old curated eligible pool, derived
preferred pool or starter pool loses an entry. All Alchimie recipes/routes remain
exact, target-reachable and within their existing bounds. All 100 Lanț route profiles
remain exact. Each of the 50 added directed links supports an actual typed one-move
API win; 44 required a node absent from the baseline and six join existing nodes.

One Lanț initial menu changes: `lt_gastronomie_220` gains Chec as a sixth option.
Aluat and Cozonac remain its two visible shortest first hops. Across all 100 records,
206 shortest first hops remain visible, with none lost and no menu-bound violations.
This is retained guidance, not a new route-diversity improvement claim. Actual menu
labels were resolved with the same neighbor-aware resolver used by typed moves.

The inverse receipt reconstructs the exact V86 artifact bytes. It records nine added
nodes, 50 added edges, 28 old node degree updates, zero changed/removed old edges and
180 unchanged legacy puzzles. The pack adds six Contexto records; rankings add six
rows and update 209 old rows. Those ranking changes are separate from authored content.
The derived file changes source-binding metadata while all 336 full rows stay exact.

## Measured improvements and tradeoffs

Biscuit was absent from the old approved-target matrix, so its comparison uses the
separately captured V86 private target baseline and source-bound V87 raw review.
The V87 Biscuit probes were taken after graph application and **before** the five
feedback corrections, audit-only change and projection isolation guard. Their original
stage hashes remain in `core-associations.json`, separately from final source hashes.
None of the five exact scopes targets Biscuit; native ingredient scoring is unchanged
and the guard only changes projected scoring. The new Tort column has separate actual
evidence, and the final public Biscuit journey passes in the 56-case snack suite.
No second complete Biscuit matrix is claimed. Its incoming links grow from five to eleven.

| Guess → Biscuit | V86 | V87 |
|---|---|---|
| Făină | 147, four hops, lukewarm | 4, one hop, hot |
| Unt | 701, five hops, cold | 4, one hop, hot |
| Zahăr | 691, five hops, cold | 4, one hop, hot |
| Cuptor de bucătărie | 181, four hops, lukewarm | 4, one hop, hot |

The separate new-target review found and repaired five defining missed cues:
Pandișpan→Chec, Biscuit→Pișcot, Prăjitură→Cremșnit, projected Tort→Tort Diplomat
and projected Ciocolată caldă→solid Ciocolată. Each finishes at rank 2/hot without
changing the submitted identity or granting a win. The final composition control
keeps Tort→Cremșnit cold at rank 255; it cannot inherit the native Prăjitură exception.
See [feedback corrections](feedback-corrections.json) and
[the independent isolation review](../feedback-isolation-review.json).

The old-target matrix contains **6,941 changed and 2,146 exact observations**.
There are 2,330 newly accepted observations, 466 deliberate Chec/Brioșă identity
migrations, and no previously accepted input becomes unaccepted. Among inputs accepted
in both versions, 400 temperatures and 392 distances change. Another 4,152 changed
observations retain their temperature and distance. These counts include rank movement
and vocabulary acceptance; they are not counts of proven quality improvements.

Native ownership removes false bread-projection affinities: Chec→Zacuscă falls from
rank 9/hot to 531/cold. It also introduces a real bread-family regression:
**Brioșă→Pâine falls from 2/hot to 424/cold**, while Chec→Pâine becomes 193/lukewarm.
Brioșă's hidden target is deferred, but the valid typed input still has this weakness.
Of 42 old warm/hot observations that cool, 34 come from the two identity migrations;
the remaining eight retain their graph distance and cross a rank boundary. Examples
include Zahăr→Înghețată 66→71 and Unt→Amandina 66→73, both warm→lukewarm.
[All 42 observations](cooler-old-target-cues.json) remain visible for later review.

Bare `bicarbonat`, `bicarbonat de sodiu` and `gelatină` remain unresolved controls.
Their qualified food senses are native inputs. Generic `tort` is a Contexto projection,
not a new KG node, alias or winning equivalent. Chec and Brioșă retain native identities.
The 467 live projected terms and four exact native-replacement audit tuples keep the
existing audited vocabulary floor without inventing filler terms.

## Reproduction and compatibility

[capture-receipt.json](capture-receipt.json) binds the inputs, sources and raw captures;
[summary.json](summary.json), [core-associations.json](core-associations.json) and
[lant-guidance.json](lant-guidance.json) preserve compact evidence. Raw full matrices
survive in lossless gzip archives under `raw/`, with timestamp zero and both decoded
and archive hashes in the receipt. All three captures are retained, including the
original baseline needed to verify the 8,388 reused observations. The original focused
compatibility and followup logs are also archived and bound in their receipt.
The exact capture/comparison scripts, artifact-delta generator and
current-content measurement script are archived beside this report.

To reproduce, extract the archived `.py.txt` scripts into task scratch, check out the
explicit baseline and candidate separately, and run `capture.py --root CHECKOUT
--out CAPTURE.json --inputs inputs.json`. For the candidate, also pass
`--baseline-pack BASELINE_GAMES_PACK.json` to retain the same old-target/profile scope.
Run `compare.py BASELINE_CAPTURE CANDIDATE_CAPTURE COMPARISON.json`. The optional
`--reuse-profiles` mode rejects any source or audited-pack mismatch. The delta generator
takes `--root CHECKOUT --baseline daae025b19517c18cba2f46c6b11ea4991d9a19c --out RECEIPT`.
The measurement script only reports values; current expectations were manually reviewed
and written as immutable literals in `tests/current_content.py`.

Historical inverses now reverse V87 before the existing V86→V24 chain. V86's 468
projection rows are restored by removing the exact new Tort row and restoring Brioșă
and Chec at their original positions/IDs. The original six native exact pairs and two
projection neighborhoods remain closed historical sets; current behavior keeps all
nine native pairs and four neighborhoods under explicit checks.

Focused compatibility ran **197 cases: 196 passed and one historical test failed**
because it indexed the new Tort row in a frozen V85 vocabulary. The fix compares the
reconstructed V85 rows with its exact retained 469-row set; live no-scoring metadata
and native-resolution checks remain. The affected module then passed all **57 cases**
in 7.460 seconds. Original failure evidence is preserved. The independent snack lane
also passed all **56 V87 cases**, including both historical inverses and six public
journeys. See [focused-compatibility.json](focused-compatibility.json).

Full integration is recorded by root. These checks do not establish human enjoyment,
universal semantic ranking quality, public beta acceptance or production readiness.
