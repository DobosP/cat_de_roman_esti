Valid until: bound content, runtime, reviews or UI change — then treat as history and repeat affected checks.

V94 starts from `c971846`, after the requested V93 main landing. It adds twelve reviewed
rounds/targets, seven Alchimie words, seventeen recipes and clearer Lanț connections.
Current integration results and artifact pins belong in [STATUS](../../STATUS.md).

| Game | Accepted additions | Content |
|---|---:|---|
| Conexiuni | 1 board | Lower-limb parts, printed publications, calendar units and household/preparation senses of *a bate* |
| Cald sau Rece | 2 targets | Ciorbă de perișoare and Temă pentru acasă |
| Lanțul Cuvintelor | 1 round | Ciorbă de perișoare → Sarmale, through meat or rice |
| Intrusul | 4 boards | Sleeping objects, milled cereals, interior rooms and writing supplies |
| Perechi | 4 boards | Sixteen new practical associations, including nail/pincers and milk/whey |
| Alchimie | 7 words, 17 recipes | Cartofi gratinați, Chiftele de pește, Crochete de cartofi, Jeleu de fructe, Paste cu pesto, Piure de dovleac and Tzatziki |

Conexiuni introduces twelve words previously unused in that game's boards; Intrusul
introduces sixteen and Perechi twenty-three. These are per-game vocabulary exposures,
not new shared KG nodes. Alchimie's seven words are original world-local definitions;
the shared KG and its typed forms remain unchanged.

## Content quality and rejection

All five raw pack proposals received independent factual/quality review before pending
staging. Fresh allocated dossiers included the final connection wording. Final review
promoted four records and rejected `lt_geografie_242` (Sfinx→Crucea Caraiman).

The monument owner's account places the cross on a secondary summit and gives its
height including the base. The old KG description instead says Șaua Caraiman and 28m.
A reviewer initially assumed that description was unused. [Actual GET and rendering
checks](pack/public-description-rejection.json) showed it is visible, so both final
judgments reject the new round. Original judgments and the correction are preserved;
the rejected ID stays reserved and [reimport/history checks](history/binding-report.json)
bind its durable tombstone. Existing approved stock and the KG were not rewritten.

The accepted [BFF audit](pack/independent-final-api.json) selects every new record
through public category/difficulty/seed requests and wins, including both food routes.
Invalid inputs, repeats, hints, GET and terminal state are checked. Rice is a documented
optional perișoare ingredient, not a universal requirement. Homework is an ordinary
assigned task; no legal homework rule is embedded. Vioară was excluded because obvious
neighboring-instrument guesses produced poor feedback despite numerical density.

All eight quick boards have complete independent semantic review and original mechanics/
rating checks. All 65 previous authored records and payloads/scores remain exact.
[Final winning audit](quick/live-audit.json) covers all 73 authored boards through natural
seeds. The separate final-quality recovery checks cover wrong answers, repeats, hints,
GET and completion for each addition. All eight additions qualify for starter selection.
The 336 core boards remain exact.

Alchimie grows 235→242 concepts, 315→332 recipes and 131→138 craftable discoveries.
Alternative-result count grows 86→92; crafted intermediates grow 57→61. Compot and Sos
de iaurt gain onward uses. New Jeleu de fructe and Piure de dovleac are useful ingredients
for existing preparations; pesmet also gives an additional Cașcaval pane route.
Every old concept/recipe record, eight starters, 96 later supplies, twelve tiers and
32 goals remain exact. Six historical saved-book generations preserve every earned
prefix, including all 131 entries of a completed V93 collection. [Live world audit](alchimie/live-audit.json)
and both final reviewers bind the exact installed catalog and runtime.

## Connection wording and interface

Two independent review batches approve 21 short noun phrases bound to complete existing
edge snapshots. They explain publication, literary membership, posthumous Academy
membership, place, ingredients and nearby landmarks. All eighty earlier captions are
unchanged. Bidirectional text stays truthful; changed or missing edges fall back safely.

The second batch's initial plateau wording was corrected to **stânci și monument din
Bucegi** after the monument owner's source distinguished plateau access from the actual
summit location. That caption is independently valid for an existing edge; it does not
approve the rejected new round or its incorrect target description.

The mobile critique found earned paths wider than the screen with a hidden horizontal
scrollbar. Scoped Lanț wrapping now keeps complete relation phrases and node labels
readable at 320px with doubled text, while preserving keyboard focus and gameplay.
[Implementation verification](gui/independent/final-review.json) records 22 desktop/mobile
journeys; [a separate reviewer](gui/final-independent-review.json) independently checks
source, captures and three fresh keyboard/reload/undo journeys. No additional player
controls or requests are introduced. This is browser evidence, not human enjoyment or
physical-device acceptance.

## Preservation and evidence

The [five-core-artifact inverse](artifact-delta.json) restores exact `c971846` bytes
before older checks. The ledger inverse restores the exact original 104 entries;
current 105-entry tests separately verify the rejected round and its gate provenance.
Every previous pack payload, world record and authored quick score stays intact.
Private ranking/selection metadata is allowed to recompute as the pools grow.

[Contexto profile proof](contexto-profile-delta.json) retains all 259 previous target
profiles exactly and accounts for two additions. The generated browser seed snapshot
changes only Lanț, preserving the other five games and the original full fixture.
[Content delta](content-delta.txt) separates additions from metadata changes.

[Archive manifest](archive-manifest.json) maps exact source bytes to archived evidence,
with explicit source/archive sizes and decoded hashes for lossless compressed logs.
Python author/reviewer scripts are stored as text. Bound final and baseline captures
are retained; unbound intermediate browser trace ZIPs remain scratch diagnostics.
Final gate results and publication state are recorded separately in STATUS.

## Final integration

[The final receipt](verification.json) records **2133 backend and 53 account tests on
each Python version (3.12 and 3.14)**, **510 browser checks** and **212 native frontend
checks**. Both validators, Ruff, frontend lint/typecheck/build, documentation and staged
whitespace checks pass. Initial JS/CSS gzip remains **119.23/120 KiB**.

The first full browser run passed 506 and exposed two old keyboard-focus expectations.
Pesto now has an onward recipe and correctly remains selected after crafting. The
updated test checks that continuation and adds a separate Lipie+Friptură→Șaorma case
for collection-focus fallback after both inputs are depleted. All six focused cases and
the final 510-case browser run pass; application/data/approval inputs did not change.
The [69-file ledger](gate-inputs.json) records the test-only amendment and preserves
all 68 earlier changed inputs exactly. Both Python results remain current.

[Preview checks](preview-check.json) verify the final 242-concept/332-recipe world and
matching emitted asset on 8150. Landed V93 remains available on 8160. V94 is a verified
local candidate; no V94 main merge, push, deployment or automatic next session occurred.
