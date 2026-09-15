Valid until: bound content, runtime, reviews or UI change — then treat as history and repeat affected checks.

V95 follows the requested V94 landing. Its baseline is main `cf6b28b`, whose
[GitHub checks passed](https://github.com/DobosP/cat_de_roman_esti/actions/runs/35018580589).
This version adds thirteen rounds/targets, five Alchimie words and ten recipes,
plus visible memory of unsuccessful Alchimie pairs. Current verification and publication
state belong in [STATUS](../../STATUS.md); the decision is [ADR-0153](../../adr/0153-expand-discovery-and-remember-attempted-pairs.md).

| Game | Accepted additions | Content |
|---|---:|---|
| Conexiuni | 1 board | Boiled grains, bread spreads, light sources and meanings of *coadă* |
| Cald sau Rece | 2 targets | Penar and Clește |
| Lanțul Cuvintelor | 2 rounds | Oven → crumb; powdered sugar → Tort Diplomat, each through two separate intermediates |
| Intrusul | 4 boards | Workshop tools, body parts, tableware and floor cleaning |
| Perechi | 4 boards | Sixteen everyday associations across home, school, food and nature |
| Alchimie | 5 words, 10 recipes | Budincă de paste, Cremă de zahăr ars, Negresă, Pavlova and Profiterol |

## Content review

The new Conexiuni board exposes nine words previously unused in that game; Intrusul
exposes ten and Perechi twenty-three. These are per-game exposures. Shared KG identities,
links and forms remain exact. Five raw pack proposals passed separate factual/quality
review before pending staging, then independent allocated-ID judgments and strict gates
promoted all five. Public definitions and actual displayed relationship text were read.

Penar has strong school and writing-item routes. Clește has hot metal, hammer and
screwdriver guesses, but unealtă, fier and scule remain unknown; atelier and foarfecă
are lukewarm. Both reviewers accepted the useful alternative approaches and retained
these dictionary gaps explicitly. No graph changes artificially improve the results.
New Lanț paths remain legible through familiar objects, but their actual captions are
mostly generic. Detailed private edge explanations were not mistaken for displayed text.
The 101 existing custom captions remain unchanged.

The final anonymous-selection audit exposed a blocker: the beginner selector always
replaced either new two-route round with an existing wider round. Its original failure
is retained. Casual selection now occasionally honors the initial eligible narrower pick
(one in four when such a pick occurs), while continuing to favor wider choices. Daily
selection and the strict two-route content floor stay unchanged. Independent source,
distribution and natural-play checks cover the corrected selector.

All eight quick boards receive complete independent factual and quality review. The
73 previous authored records and scores remain exact, as do the 336 core boards.
Seven additions qualify as starters. The tableware Intrusul board remains playable
and preferred but lacks the native Farfurie–Castron edge required for starter admission;
no threshold was weakened. Final audits cover natural selection, winning paths and
wrong/repeated answers, hints and reload recovery.

Alchimie grows 242→247 concepts, 332→342 recipes and 138→143 discoveries. Every new
result has two recipes. Alternative-result count grows 92→97 and intermediates 61→63:
Bezea and Paste cu brânză gain onward uses. The five additions themselves are terminal
results; they do not all deepen the graph. Original explanations name additional
ingredients, baking, cooling and assembly where needed. Factual checks include original
Romanian recipes and cross-generational recognition evidence.

All 242 prior concepts and 332 prior recipes remain exact. Eight starters, 96 later
supplies, twelve tiers and 32 optional goals are unchanged. Seven previous saved-book
generations preserve earned entries, including all 138 discoveries from a complete V94
collection. Both final reviewers approve the exact catalog and live-audit bindings.

## Alchimie interaction

After a failed combination, selecting either ingredient marks its tried partner with
*Încercat*. Immediate retries show a pair-specific acknowledgment without another request
or save write. The pair remains selectable, including by keyboard and drag. Memory is
limited to 128 unique observed pairs per server session; it exposes no untried recipes.

The server records only confirmed empty results. Reload and goal changes retain memory;
new/restored sessions and recipe-book changes clear it. Local acknowledgments expire
30 seconds after the last authoritative state, so a newly available recipe can be tried.
A review caught the original indefinite-cache risk. A later keyboard check found a
stale focus reference after two identical cached retries and a lost response. Cached
acknowledgments now retain the already focused button and center it directly, without
queuing deferred focus. The bounded version was then checked
independently. Cached acknowledgments also obey save ownership and request locks.

[Independent browser review](gui/independent-browser-final/review.json) verifies seven fresh
scenarios against the landed baseline, including reversed/drag repeats, keyboard focus,
320px with doubled text, committed/uncommitted lost responses, expired restoration and
freshness expiry. Repeating an empty pair uses one POST instead of two. Backend tests
check bounded memory and an actual compatible-book upgrade that adds the former empty
pair. These checks establish behavior, not measured human enjoyment or device acceptance.

## Preservation and evidence

[The five-artifact inverse](artifact-delta.json) reconstructs exact `cf6b28b` bytes before
historical checks. All 705 previous pack records remain exact; ranking metadata recomputes.
The 105-entry rejection ledger, KG/mobile artifacts and earlier review pins remain exact.
[Contexto profiles](contexto-profile-delta.json) preserve all 261 previous target profiles
and account for exactly two additions. Original browser seed snapshots are archived.

[Archive manifest](archive-manifest.json) maps source bytes to archived evidence. Python
scripts are preserved as text; logs with whitespace-sensitive output are losslessly
compressed. Initial failures and corrected verification are retained. Temporary Python
environments, browser traces and test working directories are not review inputs.
[Final verification](verification.json) binds the tested inputs, results and installed
artifacts. The owner subsequently authorized landing V95 and starting V96. Production remains
anonymous V91.
