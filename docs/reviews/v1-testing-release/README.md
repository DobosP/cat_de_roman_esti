# V1 testing release (internal wave V100)

Valid until: the next change to the reviewed V1 source or artifacts — then treat as history.

Baseline: local V99 `cc0a6a490f4a37f6f94b59cf9a84eb760cb3a401`.
Requested audience: mixed ages, phones and desktop browsers. Decision: [ADR-0158](../../adr/0158-v1-testing-release.md).
Current release status and completed gates live in [STATUS](../../STATUS.md) and
[verification](verification.json). The Romanian [tester guide](../../TESTARE_V1.md)
covers all six games, recovery, enlarged text and specific feedback.

## Interface

V1 / package 1.0.0 puts the six descriptive game choices before daily progress.
Circuit links carry daily intent into an explicit daily start, while an existing
saved round keeps its normal recovery flow. Rules are available directly; empty
options are gone. Quick games describe their remaining mistake budget correctly.
Replay is the primary result action. At 320 px with 200% root text, Conexiuni uses
two columns and the quick games can use one, preserving readable long words.
Normal-size desktop and phone layouts retain their intended columns. A denied browser
storage getter cannot abort startup. Automatic reload requires a persisted loop guard;
failed game routes offer explicit recovery while preserving saved rounds. A failed
Alchimie new-round request keeps its retry control and error visible together without
changing focus or the retained round. Lanț displays its authoritative current word
immediately, so a delayed animation cannot retain the previous position after recovery.

The source audit drew interaction ideas from the official [Waffle](https://wafflegame.net/)
page (clear objective, remaining moves, help and next actions) and
[Little Alchemy 2 hints](https://hints.littlealchemy2.com/) (optional help and free exploration).
These are design inferences; no artwork or implementation was copied. NYT Connections
and Contexto could not be meaningfully inspected through retrieval and are not
claimed as inspected references. [Source audit](ui/source-audit.json) records access
and the six-game rationale. [Capture scope](ui/capture-scope.json) separates real game
content from injected long-label stress cases; physical devices and human enjoyment are untested.

## Content decisions

The [stock audit](content/current-stock-audit.json) mechanically covers all 716 pack
records, 421 stored quick boards, 80 approved Alchimie projections and 351 exploration
recipes. Editorial sampling covers 38 pack boards, 27 quick boards and 16 exploration
recipes. This is not an independent editorial approval of every stored board.

Seven exact [factual repairs](content/factual-repair-proposal.json) correct Caraiman,
the Village Museum, the Athenaeum, three Neagu relationship labels and one false
Operațiunea Monstrul–Dem Rădulescu casting edge. The author and independent factual
and quality reviewers are recorded in the bound proposals. The guarded generator
preserves all 180 KG puzzles and atomically writes both fixture copies.

A separately reviewed [selection reserve](content/selection-reserve-quality-review.json)
excludes 23 exact boards from new bundled V1 rounds: four sparse Cald targets, four
ambiguous or mirrored Conexiuni boards, twelve Alchimie challenges with only one
productive opening, and three quick boards with a misleading Latin-origin explanation.
Stored records remain available for historical inspection. The manifest is bounded,
digest-pinned and matches exact definitions. Custom pack/KG development overrides
retain their previous unranked compatibility behavior outside the bundled release.

The [held/rejected audit](content/held-rejected-audit.json) revisits all 256 historical
final rejections and eight pending pack records, plus the V98/V99 research pools.
Only `lt_viata_de_roman_211` (Ghiozdan → Capra cu trei iezi) is newly promoted, after
three reviewed captions, a fresh dossier and independent analyst/verifier acceptance.
Both two-step routes win through [normal API selection](content/reconsideration/natural-selection-api.json).
All 256 rejections remain rejected; seven pending records remain pending. Correct
captions did not rescue the other held boards automatically. No research-only concept
or rejected recipe was installed.

## Downstream preservation

The [graph audit](content/factual-downstream-audit.json) checks every Cald target against
all 2,416 guesses, all 123 Lanț records, all 245 Conexiuni records, 421 quick boards,
80 Alchimie cores and the complete exploration world. Removing the false casting
edge causes two raw Cald similarity changes, 275 resulting rank-feedback shifts and
one temperature change; the counterfactual attributes all of these to that deletion.
Lanț shortest routes/par/openings stay exact; 30 deeper menu states across 17 boards
lose the false hop or its prefixes. No unexpected reachability change was found.

The original graph audit deliberately ends with a recipe-snapshot hold: three corrected
metadata snapshots disable seven previously accepted additions under the old catalog.
The fresh [recipe proposal](content/recipes/catalog.json), independent reviews,
[live audit](content/recipes/live-audit.json) and
[supplemental closure](content/recipes/downstream-closure.json) resolve that hold.
All 68 selectable books retain their exact pre-V1 recipe maps, routes and par, including
those seven additions. The refreshed catalog carries 49 published additions across
27 boards; one old addition belongs to a now-reserved challenge and is withdrawn.
47 candidate rows are exact; two retain the same recipes but remove already-rejected
competitor references, with the original rejection reasons explicitly preserved.
The 80-row raw live audit includes the twelve archived reserve boards and is not a
claim that those boards remain selectable. Its final frontend source binding was
refreshed after the retry-visibility fix; all board audit data stays exact. Earlier
review bytes are retained under `content/recipes/before-retry-visibility/`. The
[incremental source review](incremental-source-review.json) covers that UI change.
The separate [Lanț source review](lant-current-position-source-review.json) covers its
current-word rendering fix; verification records the old-bundle failure and final checks.

The [quick carry-forward](content/quick/catalog.json) refreshes source/review bindings
for the same 85 authored boards. All 85 are independently replayed through natural
selection, win and GET recovery. The frozen 336 quick payloads stay exact.
The exploration world stays at 251 concepts / 351 recipes / 147 discoveries, including
nine historical books and 1,009 saved prefixes. Session, history and request bounds
are unchanged. Recipes and unrevealed answers remain server-side.

[Artifact delta](artifact-delta.json) reversibly binds the five changed core artifacts
to the exact Git baseline. Historical tests reconstruct their historical source bytes;
their old approval/hash assertions are preserved rather than updated to today's data.
The supplemented catalogs keep independent carry-forward evidence alongside this delta.
Archive-specific Git attributes preserve original reviewed bytes on all hosts, including
native-generator CRLF dossiers; real trailing whitespace remains checked.

## Release inventory

| Game | Stored | Approved | Pending | New-round pool |
|---|---:|---:|---:|---|
| Conexiuni | 245 | 245 | 0 | 83 eligible |
| Cald sau Rece | 265 | 263 | 2 | 255 eligible |
| Lanțul Cuvintelor | 123 | 121 | 2 | 121 eligible |
| Alchimie challenges | 83 | 80 | 3 | 68 eligible |
| Intrusul | 228 | 228 | 0 | 226 selectable; 188 preferred |
| Perechi | 193 | 193 | 0 | 192 selectable; 153 preferred |

Pack: 716 records = 709 approved + 7 pending; 527 eligible rounds. Quick games:
421 stored / 418 selectable / 341 preferred. Starter pools remain 62 Intrusul / 61 Perechi.
The graph has 2,416 concepts, 9,458 edges and 8,641 accepted forms. These totals
describe curated records; existing on-demand fallback generators remain available
when a requested shelf has no eligible curated round. Generated rounds are not
counted as individually reviewed catalog records.

## Verification scope

Complete backend: 2,446 passed; accounts: 53 passed; frontend unit: 224 passed.
Browser coverage comprises 588 distinct verified cases: the complete 586-case run
(583 passed, three failures subsequently resolved), followed by all 142 affected
cases passing on the final build with one worker and no retries. This is composed
coverage, not a single all-green 588-case invocation. The
[harness review](recovery-harness-source-review.json) preserves request/focus invariants;
[resource forensics](browser-affected-run-forensics.json) distinguishes host failures from
application defects. All required lint/build/content/docs gates and isolated-wheel
smoke checks pass. The independent [final integrity check](release-integrity-check.json)
confirms the bound source, archive bytes and exact browser coverage.

See the exact commands, results, source/artifact hashes and preserved intermediate
failures in [verification](verification.json). Browser runs use Microsoft Edge on
Windows, with desktop and Pixel 7 emulation, plus 320 px enlarged-text checks.
The complete Linux suite uses the unchanged repository tests under WSL; targeted
native tests exercise the deploy-version Python as well. A technical pass does not
establish human enjoyment, age suitability for every concept, or physical-device acceptance.

This release is prepared locally. Production remains at its previously recorded version;
no origin push, deployment, accounts activation or recurring loop restart is included.
