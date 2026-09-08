# Independent V89 feedback-cost review

Valid until: the bound baseline, proposed pair or final implementation changes — then treat as history.

**Recommendation: add only the native Tort Diplomat→Frișcă exact nonwinning pair
for this pastry repair. Keep the graph and the sour/sweet cream distinction intact.**
This is a source-backed culinary association and an explicit editorial ranking choice;
recipes do not establish that the correct numeric rank must be two. Final code and
integration still require review. The associated JSON binds the inspected baseline.

The independent reproducer made 15 fresh private-BFF first guesses and deleted all
15 sessions. It reconstructed both forward shortest paths and globally minimum-weight
paths from actual non-distractor service adjacency. These are the winning paths under
the current algorithms, rather than a plausible path found by hand. Ties choose
lexicographic node IDs. Both metrics and all edge records survive in
[feedback-path-probes.json](feedback-path-probes.json); the reproducible script is
[trace-feedback.py.txt](trace-feedback.py.txt).

| Native guess toward Frișcă | Current result | BFS / minimum weight | Exact scope recommendation |
|---|---|---|---|
| Tort Diplomat | 345 / Rece | 5 / 5.82 | Accept one nonwinning pair |
| Zacuscă | 24 / Cald | 3 / 3.48 | Preserve as unresolved hub noise |
| Cremșnit | 504 / Rece | 5 / 6.02 | Do not add an equally strong exact pair |
| Pișcot | 944 / Foarte rece | 6 / 7.02 | Do not infer an ingredient identity |
| Prăjitură | 181 / Călduț | 4 / 4.82 | Too broad for a universal override |
| Smântână, the fermented owner | 34 / Cald | 3 / 3.60 | Preserve corrected ownership |
| Smântână dulce pentru frișcă | 2 / Fierbinte | 1 / 1.20 | Preserve the direct source relation |

## Fact and ranking are separate

[Gina Bradea's original Diplomat recipe](https://pofta-buna.com/tort-diplomat-reteta-clasica/)
uses whipped cream in its defining mousse, with fruit and either sponge or ladyfingers.
[BărbatLaCratiță's independent original recipe](https://www.barbatlacratita.ro/2012/12/tort-diplomat-reteta.html)
also whips the liquid cream before combining it with the cooled filling. Its optional
outer decoration does not negate the cream inside. These two original recipes support
a specific prepared-dessert/component association. The current graph already contains
Frișcă→Diplomat as an ingredient relation; a Contexto-only reverse cue avoids changing
Lanț/Alchimie directionality or pretending the cake and whipped cream are synonyms.
The existing Savarină→Frișcă exact pair supplies a comparable reviewed pattern.

Cremșnit has credible whipped-cream variants, including
[Gina Bradea's layered version](https://pofta-buna.com/cremes-prajitura-foietaj-frisca-crema-vanilie/).
The maker's [Dr. Oetker vanilla filling recipe](https://www.oetker.ro/retete/r/crema-de-vanilie-pentru-cremsnit-crema-fiarta)
instead uses eggs, milk, flour, butter and sugar without whipped cream. This supports
variant-specific association, not a requirement that all Cremșnit share Diplomat's
near-target treatment. Likewise,
[the original Savoiardi recipe](https://pofta-buna.com/piscoturi-de-sampanie-savoiardi/)
defines a separately baked egg/flour/sugar biscuit; using it alongside whipped cream
in an assembled dessert does not make the biscuit itself whipped cream. These
rankings remain semantic quality costs, not facts declared correct by a passing test.

## Why Zacuscă is warm

The exact shortest and weighted route is
**Zacuscă→Bucătărie→Frigider→Frișcă**. Its edges are de3776
(`se prepară în`, strength0.74, bidirectional), de8103 (`se află în bucătărie`,
strength0.98, bidirectional, stored Frigider→Bucătărie), and de8681
(`păstrează la rece`, strength0.80, one-way Frigider→Frișcă).
These relations are individually coherent. Their short location/storage chain makes
an unrelated food warmer than a genuinely cream-based dessert. I found no factual
wrong edge in this winning chain that justifies deletion. This is a consequence of
hub connectivity and the current hop-first ranking, not a proxy or synonym error.
A broad relation-aware scoring experiment may eventually address it, but requires
its own baseline and cross-game review. A Zacuscă blacklist or removal of truthful
kitchen/fridge links is not justified here.

Diplomat instead takes Desert→Cozonac→Bucătărie→Frigider after its initial edge.
Cremșnit takes Prăjitură→Cozonac→Bucătărie→Frigider. Pișcot first reaches Diplomat
and then follows its route. All three current minimum-weight paths also have their
minimum hop count. The new exact pair should alter feedback for the submitted native
Diplomat owner toward Frișcă only, preserve native identity and exact Frișcă wins,
and not cascade through the projected `tort` fallback or other cakes.

## Household interpretation

The 71 existing closed policies remain part of actual scoring: Făraș/Mop/Aspirator
borrow Podea and Burete de vase/Detergent borrow A spăla outside exact wins.
Fresh probes find Mătură→Aspirator4/hot, Făraș→Mătură4/hot,
Mop→Aspirator3/hot and Burete de vase→Detergent4/hot. The last three are
proxy-aware results, so raw native-hop counts alone are insufficient for candidate
judgment. Scaun→Taburet2189/frozen remains a real cue weakness: its seven-hop route
travels through culture/music and Pian. This supports keeping the hidden Taburet
target held, not restoring broad Casa/Aspirator approximations.

This review did not edit runtime, graph or tests, promote rounds, rerun the full
V88 matrix, or perform human playtesting. Source pages were opened on2026-09-08;
Savori Urbane returned403, so its search snippets were not used as acceptance evidence.
