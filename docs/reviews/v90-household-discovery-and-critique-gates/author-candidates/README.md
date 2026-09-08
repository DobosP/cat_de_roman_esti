# Household discovery — author proposal

Valid until: independent V90 graph/content judgments and final dossiers supersede this
proposal — then treat as history.

Author draft: **3 native concepts, 17 directed links, 10 stored grammatical forms,
0 reviewed synonyms and 3 existing-object Contexto candidates**. This is proposal scope,
not approval, application, eligibility or human playtesting. The graph payload is
[graph-proposal.json](graph-proposal.json), SHA-256
`672ea9f249ec9f18dbc51c24427580b61e98abbaef2b7b3a6d0fd5c557d395ba`.
[Source notes](sources.json) contain short author paraphrases and exact original URLs;
[edge-source-map.json](edge-source-map.json) binds the 17 ordered triples to those notes.
No runtime, test helper, generated fixture or static asset is edited by this author.

## Useful meanings before hidden targets

Praf models ordinary dust suspended in air or settled on household surfaces. Its four
cleaning-tool uses and the carpet-fibre source provide five incident neighbors, all in
`viata_de_roman`. Firimitură connects bread/biscuit breakage with collection of dropped
crumbs, crossing food and household use: four incident neighbors, two gastronomic.
Scamă links clothing, a blanket and some carpets to loose textile fibres and vacuum
collection: four incident neighbors, all household. These counts use distinct playable
neighbors; their actual incoming counts are only **1/2/3**, so **none of the three new
concepts is proposed as a hidden Contexto target**. Four-incident/two-same-category
preflight is different from Contexto's five-incoming floor.

The description and source labels deliberately distinguish dry floor debris, fibres
in some textiles and microfiber-mop dust collection. Every new edge is one-way and
non-distractor. Strengths 0.70–0.90 are editorial estimates, not measured source values.
No inferred reverse edges, blanket material claims or food-making recipes are authored.

## Forms and Praf ownership boundary

- Praf: `praful`, `prafului`; **no** `prafuri`, powder synonyms or named powders.
- Firimitură: `firimituri`, `firimiturile`, `firimiturii`, `firimiturilor`.
- Scamă: `scame`, `scamele`, `scamei`, `scamelor`.

The accent-insensitive resolver already accepts articulated `firimitura`/`scama` through
the labels; storing those strings would add no new normalized recognition. No redundant
forms are proposed. Dictionaries list other variants/senses, which are not automatically
accepted as synonyms. `păr`, `curent`, `pulbere`, `murdărie`, `sac`, `filtru`, activities,
Pardoseală/Podea equivalents, diminutives and bathroom/kitchen sink ownership are held.
Pulover appears in a source but is not native; this proposal uses existing Pătură and
adds no Pulover node just to increase density.

[Praf's existing projection](../../v89-feedback-and-conexiuni-recovery/praf-review.md)
has public ID `ctxp_81703160cad7893fa1c9`, Pământ fallback and exactly three V89 tool
scopes. The native label deliberately collides with that projected surface, so graph
application alone is not a complete safe migration. Root must choose and independently
review public identity/attempt continuity, fallback, private-target and typo behavior
before accepting the runtime combination. Praf de copt, Lapte praf and every other
native owner stay separate. The author makes no promise that historical Praf scores
stay exact merely because the source row remains. Native recognition precedence is
an observed implementation concern, not permission to bypass the migration review.

## Exact source-backed links

| Index | Directed association | Meaning and principal original source |
|---:|---|---|
| 0 | Praf → Făraș | Dry sweepings gathered in a dustpan; Leifheit + DEX object definition |
| 1 | Praf → Mătură | Dust swept from floors; Leifheit dry cleaning |
| 2 | Praf → Mop | Microfiber mop can collect floor dust; Vileda Turbo |
| 3 | Praf → Aspirator | Household dust vacuuming; Kärcher + DEX |
| 4 | Pâine → Firimitură | Pieces left when bread is cut or broken; DEX |
| 5 | Biscuit → Firimitură | Crumbs from biscuit breakage/eating; Kärcher carpet care + DEX |
| 6 | Firimitură → Făraș | Dropped crumbs collected from floors; Leifheit |
| 7 | Firimitură → Aspirator | Dropped crumbs vacuumed from floors/carpets; Kärcher |
| 8 | Haină → Scamă | Clothing can shed textile threads; Philips + DEX |
| 9 | Pătură → Scamă | Blankets can form loose textile threads; Philips + DEX |
| 10 | Covor → Scamă | Some carpets, particularly wool, shed fibres; IKEA |
| 11 | Scamă → Aspirator | Loose floor/carpet lint is vacuumed; Kärcher + IKEA |
| 12 | Covor → Aspirator | Periodic vacuum care; Kärcher + IKEA |
| 13 | Electricitate → Aspirator | Operating energy from mains or battery; original Kärcher manual/family |
| 14 | Farfurie → Burete de vase | Manual dishwashing with a surface-appropriate sponge; FINO + DEX plate |
| 15 | Apă → Burete de vase | Water wets/rinses a dish sponge; FINO + Vileda |
| 16 | Covor → Praf | Carpet fibres may contribute to household dust; Kärcher composition explanation |

No Chiuvetă link is proposed: its existing bathroom identity cannot silently become
a kitchen sink. Electricity is not inferred from the general DEX aspirator definition;
the manufacturer's corded manual and cordless designs supply that part of the evidence.

## Measured prospective screen

The [screen](prospective-screen.json) and [capture](screen-proposal.py.txt) build an
**in-memory** prospective graph. They bind the old KG/pack and exact proposal; they do
not change shipped bytes. Eight directed profiles and 240 native-score observations
cover the three candidates, Mop and four held targets. This is scoring evidence, not
an actual browser/BFF journey or a review of root's future Praf migration.

| Target | Old incoming | Prospective incoming | Author proposal |
|---|---:|---:|---|
| Făraș | 3 | 5 | Fresh easy candidate after useful dust/crumb facts |
| Aspirator | 3 | 8 | Fresh easy candidate after dust, crumbs, lint, carpet and power facts |
| Burete de vase | 4 | 6 | Fresh easy candidate; plate-proxy limitation remains |
| Mop | 5 | 6 | Already approved V89; no duplicate round |
| Mătură | 1 | 2 | Hold |
| Găleată | 3 | 3 | Hold |
| Detergent | 3 | 3 | Hold |
| Taburet | 1 | 1 | Hold |

Raw candidates are [viata_de_roman/candidates.json](viata_de_roman/candidates.json).
Rejected V89 IDs352/354 remain historical rejections; any later newly staged IDs must
come from the supported importer. Useful new facts do not retroactively approve them.

On the prospective graph, native Praf/Firimitură give ranks4/5 for Făraș; Aspirator
receives native Praf4, Firimitură5, Scamă5, Covor5 and Electricitate5. The old main
kickoff measured Covor36/Electricitate378. These scores are not the final migration's
public contract and can change with root's accepted runtime policy.

Burete de vase has water6 and detergent4. Farfurie still uses its legacy Masă proxy and
scores16 despite the new direct edge, while dust scores14 and floor11. This is disclosed
semantic debt, not evidence to silently bypass a scorer. Independent C1–C6 review must
judge whether the target remains sufficiently legible; holding it is a valid result.
New unknown vocabulary and stronger direct associations are useful independently of
how many of the three proposed rounds ultimately survive.

## Other games and held scouts

[Held proposals](held-proposals.json) preserve the exact explored directions. The
Conexiuni screen checks **all234 pack boards plus122 durable rejected boards**. The
floor-tools quad duplicates V88 board362, and a blanket/carpet/pillow/mattress quad
shares three members with board293. Neither is a fresh group. The three new dust/crumb/
lint nodes do not form an honest four-member predicate; adding an abstract Murdărie
member to fill it would fail the nameable predicate and recognition intent. No Conexiuni
round is proposed.

Thirty-five directed Lanț endpoint combinations were inspected. Five pass a two-first-
hop/two-wide numeric screen, but that does not establish D2/D3. Pătură→Aspirator has
Scamă and Covor as two shortest intermediates, yet Pătură→Covor is only the existing
generic household-textile association. Pătură→Făraș also uses such edges and the older
Aspirator→Făraș same-task relation. Food-to-Burete routes use incidental cleaning-tool
associations. The author holds all of these instead of inventing a second good route.
No new Lanț or Alchimie round is proposed.

Graph truth is not recipe truth: multiple new incoming debris links can make common
neighbors look craftable. The root's exact comparison of all83 old Alchimie books,
100 Lanț profiles/menus and336 derived boards remains necessary before application is
accepted. No Intrusul/Perechi board count is inferred from new nodes or a catalog rebuild.
Independent graph/raw reviews, supported serial transactions, exact final dossiers,
actual BFF journeys and full frozen integration gates remain outstanding.
