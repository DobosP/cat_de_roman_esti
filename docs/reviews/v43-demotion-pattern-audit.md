# V43 demoted Conexiuni pattern audit

_Audited 2026-07-30. Report-only review; no pack, ranking, sidecar, status, or runtime
behavior changed._

## Release verdict

Keep all **67/67** ADR-0066 boards demoted. All **268/268** original four-member groups are
hard-banned from direct reuse. Four predicates remain useful as design ideas only; a group
derived from one of them must replace at least two members, sit beside three wholly fresh
groups, avoid every exact and 3-of-4 collision against the **full pack, including pending**,
stay within the member-use ceiling, and pass a fresh deterministic plus analyst/verifier
gate.

The historical census excludes the subject board itself so it can measure repetition
elsewhere. That exclusion does not apply to a future candidate: its still-approved reserve
source remains in the full inventory and makes direct reuse a 4-of-4 collision. Across the
**full pack, including pending**,
**211/268** groups collide (102 exact; 190 at 3-of-4). Across **approved inventory,
including reserves**, **200/268** collide (89 exact; 179 at 3-of-4). Against **currently
eligible runtime stock**, **90/268** collide (42 exact; 65 at 3-of-4). Exact and 3-of-4
counts overlap. Runtime-only counting would re-import both reserve and pending debt.

## Method and exact coverage

- Sidecar IDs: 67 unique; 67 found as approved Conexiuni; 0 currently
  `pilot_eligible`; 268/268 groups classified in the JSON companion.
- Existing deterministic dossier run:
  `critique_pack.py --game conexiuni --status approved --ids <all-67>`. It flagged
  duplicate groups on 66 boards, approved-stock member overuse on 59, type mix on 51,
  mirrors on 11, red-herring budget on 3, and a generic region link on 1.
- Added read-only censuses: unordered exact quads; unordered 3-of-4 overlaps; full-pack,
  approved-inventory, and eligible-runtime matches; each comparison excludes the
  subject board; normalized label/member leakage; strong `is_a`/`part_of`
  class-container groups; and mirror-pair membership from the dossiers.
- Manual-only classification was used for 24 hard-banned groups with none of those
  programmatic flags. All 268 direct-quad bans have at least one explicit reason in the
  [machine-readable companion](v43-demotion-pattern-audit.json).
- Inputs are digest-bound: pack `b2b603be2354`, demotions
  `ba9bb55b17b2`, rankings
  `d05b2aa8729a`, KG `95b7e4b0a9e5`,
  historical dossier rubric `14f8efacf32c`, and hardened release-gate rubric
  `9a443ed89a6b`.

Evidence shorthand in the coverage table is `E pack/approved/eligible exact-group count`,
`N pack/approved/eligible 3-of-4 count`, `T` type-mixed groups, `M` mirror findings, `L`
label-leak groups, and `C` class/container groups.

## Dominant failure patterns

1. **Freshness is the main debt.** A6 is primary on 36 boards and
   implicated on 67/67. The full pack contains
   102 exact-reused and 190 3-of-4-reused demoted groups; approved inventory alone
   contains 89 and 179.
   Re-labeling a quad is not new content.
2. **Association bundles replace predicates.** B1 is implicated on
   47 boards. Repeated shapes are person + work + event + place,
   show + presenter + channel, or champion + event + record + generic sport term.
3. **Types and hierarchies leak the construction.** 89
   groups are 3+1 or 2+2 type mixes; 41 put a
   class/container beside at least two of its own instances via strong KG edges.
4. **Mirrors are answer keys, not traps.** Eleven boards contain 16 detected mirror
   pair findings, covering 27 group sides:
   directors↔films, TV channels↔hosts↔shows, cities↔plants, inventors↔machines, and
   rulers↔battles.
5. **Labels leak or overpromise.** A normalized scan finds
   40 group labels containing a member label.
   Factual/predicate kills include “fără cameră de filmat”, “Cifre și metale olimpice”,
   the invented `Bucovina gastronomică` node, and putting `Substratul dacic` under
   latinity.
6. **Approved-stock saturation remains a design constraint even after runtime cleanup.**
   Current eligible usage now peaks at 7,
   but the full approved inventory still has
   65 nodes over the rubric's >8
   threshold. New authoring must census both views.

## Repeated exact-quad families

| Full pack | Approved | Eligible | Demoted | Members |
|---:|---:|---:|---:|---|
| 9 | 6 | 2 | 3 | Barabulă · Cucuruz · Curechi · Păpușoi |
| 7 | 4 | 1 | 1 | Andreea Marin · Cătălin Măruță · Teo Trandafir · Virgil Ianțu |
| 7 | 4 | 0 | 1 | București · Cluj-Napoca · Iași · Timișoara |
| 6 | 3 | 2 | 1 | Cerbul de Aur · Electric Castle · Neversea · Untold |
| 6 | 3 | 1 | 2 | Columbia - România 1994 · Cupa Mondială 1994 · Generația de Aur · România - Argentina 1994 |
| 5 | 5 | 1 | 1 | Adjectiv · Pronume · Substantiv · Verb |
| 5 | 3 | 0 | 2 | Albastru de Voroneț · Mănăstirea Sucevița · Mănăstirea Voroneț · Mănăstirile pictate din Bucovina |
| 5 | 4 | 1 | 3 | Antena 1 · Kanal D · Pro TV · TVR |
| 5 | 3 | 0 | 3 | Automobile Dacia · Combinatul siderurgic Galați · Electroputere Craiova · Uzinele Reșița |
| 5 | 4 | 2 | 2 | Balcic · Castelul Pelișor · Povestea vieții mele · Regina Maria |
| 5 | 2 | 0 | 2 | Craiova · Galați · Pitești · Reșița |
| 5 | 3 | 0 | 1 | Mihai Eminescu · Mihai I · Mihai Viteazul · Mihai din Liceenii |
| 5 | 4 | 0 | 3 | Universitatea Alexandru Ioan Cuza din Iași · Universitatea Babeș-Bolyai · Universitatea Politehnica din București · Universitatea din București |
| 4 | 3 | 2 | 1 | Adrian Minune · Florin Salam · Nicolae Guță · Vali Vijelie |
| 4 | 3 | 1 | 2 | Ansamblul monumental de la Târgu Jiu · Coloana Infinitului · Masa Tăcerii · Poarta Sărutului |

The member census shows why reserve content must remain in the authoring check even when
runtime stock looks healthier:

| Member | Demoted uses | Approved uses | Eligible uses |
|---|---:|---:|---:|
| Simona Halep | 10 | 12 | 1 |
| Masa Tăcerii | 9 | 15 | 3 |
| Teatrul Bulandra | 9 | 13 | 3 |
| Coloana Infinitului | 8 | 11 | 3 |
| Poarta Sărutului | 8 | 11 | 3 |
| Muzeul Național Brukenthal | 8 | 9 | 1 |
| Academia Română | 8 | 15 | 4 |
| Nadia Comăneci | 8 | 11 | 2 |
| Aurel Vlaicu | 8 | 15 | 2 |
| București | 8 | 18 | 1 |

## Predicate ideas — original quads still hard-banned

| Group | Predicate | Members | Strict caution |
|---|---|---|---|
| `cx_arta_cultura_005.g2` | România în patrimoniul UNESCO | Sighișoara · Delta Dunării · Ceramica de Horezu · Mănăstirile pictate din Bucovina | replace at least two members, including Delta Dunării (13 approved uses; a projected 14th blocks), then rerun every collision/member gate |
| `cx_film_tv_167.g1` | Mare, dar nu aceeași apă | Marea Neagră · Marea Unire 1918 · Ștefan cel Mare · B.D. la munte și la mare | replace at least two members; Marea Unire (11 approved uses) and Ștefan cel Mare (15) are already saturated, and one swap still fails at 3-of-4 |
| `cx_personalitati_277.g1` | Opoziție anticomunistă | Elisabeta Rizea · Doina Cornea · Corneliu Coposu · Iuliu Maniu | replace at least two members and web-reverify every biography in the derived group |
| `cx_sport_226.g1` | Supranume care au prins la popor | Regele fotbalului românesc · Eroul de la Sevilla · Tricolorii · Generația de Aur | replace at least two members; keep the nickname predicate exact and do not rebuild the familiar-moment sport template |

All **268** exact four-member sets are hard-banned for direct reuse. The four rows above
preserve only a reusable predicate idea; they do not authorize reuse of the original
four-member set. The exact per-group reason list is the `groups` object in the JSON
companion. The practical hard-ban families are:

- Enescu, Brâncuși/Târgu Jiu, Caragiale/work/characters, Bucovina monasteries, and generic
  institutions/scenes;
- rivers, lakes, four-city lists, regionalisms, place-named foods, and festival lists;
- channels, hosts, shows, films/casts, industrial cities/plants, universities, and
  rights/institutions;
- aviation pioneers/machines/physics and sport “one famous moment” clusters: USA 1994,
  Sevilla, Nadia-Montreal, Halep Slams, Popovici records, and Patzaichin-Delta-pagaie.

These are bans on the current concepts **and** on their structural templates. Swapping one
member or changing the label does not make them fresh.

## Strict rules for the next boards

1. Census unordered quads against the full pack, including pending and reserves, before
   writing labels. Reject any exact or 3-of-4 match; do not wait for the promotion lint.
2. Use at most one group derived from the four predicate ideas. Replace at least two of its
   members and make the other three groups wholly fresh. This is necessary, not sufficient:
   the full gate still decides.
3. Write each group as one sentence: “Each tile ___.” If the same verb/relation cannot fill
   the blank four times, reject the group.
4. Reject person+work/event/place “universes”, class+instances, and paired owner↔owned or
   host↔event groups. A deliberate crossing pair is enough; three correspondences is a
   mirror.
5. Ban labels containing a tile's normalized label. Avoid labels that negate facts,
   enumerate unlike nouns, or use “asociat cu”, “lumea”, “constelația”, “pe scurt”, or
   “cu adresă” to conceal a loose bundle.
6. Give every board one immediately nameable anchor, at most one deep cut per hard group,
   fewer than four plausible red herrings, and no tier inversion.
7. Prefer nodes used at most five times in current eligible stock and inspect full-approved
   use as well; projected approved use must remain at or below eight.
8. A new candidate remains pending until factual verification, deterministic zero-FAIL,
   full batch-bound analyst/verifier coverage, and the owner/orchestrator decision.

## Board-by-board coverage

| Board | Primary | Secondary | Programmatic evidence |
|---|---|---|---|
| `cx_arta_cultura_003` | A6 | B2, B6 | E 3/2/0; N 4/4/3; T2 M0 L0 C1 |
| `cx_arta_cultura_004` | B5 | A6, B2 | E 4/3/1; N 4/4/0; T2 M1 L0 C0 |
| `cx_arta_cultura_005` | A6 | — | E 3/3/2; N 3/3/2; T0 M0 L0 C0 |
| `cx_arta_cultura_007` | B1 | A3, A6, B2 | E 0/0/0; N 2/2/1; T0 M0 L0 C0 |
| `cx_arta_cultura_091` | A6 | B2, B6 | E 2/2/1; N 4/4/2; T0 M0 L0 C1 |
| `cx_arta_cultura_092` | B5 | A6, B1, B2 | E 2/2/0; N 4/4/2; T0 M1 L0 C1 |
| `cx_arta_cultura_094` | B6 | A6, B2 | E 2/1/1; N 4/3/2; T3 M0 L0 C2 |
| `cx_arta_cultura_159` | A4 | A6, B1, B9 | E 4/3/2; N 4/4/2; T2 M0 L1 C2 |
| `cx_arta_cultura_161` | B6 | A6, B2, B9 | E 1/0/0; N 4/3/1; T1 M0 L1 C0 |
| `cx_arta_cultura_162` | A6 | B6 | E 1/1/1; N 2/2/0; T0 M0 L0 C0 |
| `cx_arta_cultura_239` | A6 | B1, B2, B9 | E 1/1/1; N 4/4/2; T2 M0 L2 C2 |
| `cx_arta_cultura_241` | B1 | A6, B2, B9 | E 1/1/1; N 1/1/1; T2 M0 L2 C0 |
| `cx_film_tv_008` | A6 | B1, B2, B9 | E 3/2/2; N 0/0/0; T3 M0 L3 C2 |
| `cx_film_tv_009` | B5 | A6 | E 2/0/0; N 3/3/2; T0 M1 L0 C0 |
| `cx_film_tv_011` | A6 | B1, B2, B9 | E 1/1/0; N 1/1/0; T1 M0 L2 C0 |
| `cx_film_tv_013` | B9 | A6, B1, B2, B3 | E 1/0/0; N 2/0/0; T2 M0 L4 C3 |
| `cx_film_tv_165` | A6 | B1, B2, B9 | E 4/4/2; N 1/1/0; T2 M0 L3 C0 |
| `cx_film_tv_167` | B6 | A6, B3, B9 | E 0/0/0; N 1/1/0; T0 M0 L0 C0 |
| `cx_film_tv_169` | B5 | A6, B2 | E 3/2/2; N 3/1/0; T1 M3 L0 C0 |
| `cx_gastronomie_171` | A4 | A1, A6, B1, B6 | E 1/1/1; N 3/3/1; T0 M0 L0 C1 |
| `cx_geografie_028` | A6 | B1, B2, B9 | E 0/0/0; N 2/2/0; T1 M0 L2 C0 |
| `cx_geografie_110` | A6 | B1, B2, B6 | E 2/2/1; N 3/3/1; T1 M0 L0 C0 |
| `cx_geografie_177` | A6 | B6 | E 2/2/0; N 4/4/1; T0 M0 L0 C0 |
| `cx_geografie_178` | A6 | B1, B2, B6, B9 | E 3/3/2; N 4/4/3; T2 M0 L2 C2 |
| `cx_geografie_252` | B1 | A6, A7, B2, B6, B9 | E 1/1/1; N 3/1/0; T1 M0 L1 C0 |
| `cx_istorie_029` | B5 | A6, B2 | E 2/2/2; N 4/4/2; T1 M1 L0 C0 |
| `cx_istorie_030` | A6 | B1, B2, B9 | E 2/2/2; N 3/3/3; T2 M0 L2 C0 |
| `cx_personalitati_064` | A6 | B2 | E 3/3/1; N 4/4/1; T2 M0 L0 C0 |
| `cx_personalitati_144` | A6 | B1, B2 | E 3/3/1; N 4/4/3; T2 M0 L0 C0 |
| `cx_personalitati_210` | A6 | B1, B2 | E 2/1/0; N 3/3/2; T1 M0 L0 C0 |
| `cx_personalitati_213` | A6 | B1 | E 2/2/2; N 2/2/0; T0 M0 L0 C0 |
| `cx_personalitati_214` | A6 | B1, B2 | E 1/1/1; N 4/4/3; T2 M0 L0 C0 |
| `cx_personalitati_275` | A6 | B1, B2 | E 3/3/3; N 3/3/3; T0 M0 L0 C0 |
| `cx_personalitati_276` | A6 | B1, B2, B6 | E 0/0/0; N 2/2/1; T1 M0 L0 C0 |
| `cx_personalitati_277` | B9 | A6, B1, B2, B6 | E 0/0/0; N 3/3/2; T2 M0 L0 C2 |
| `cx_societate_065` | A6 | B2, B6 | E 3/3/1; N 4/3/1; T1 M0 L0 C0 |
| `cx_societate_067` | B5 | A6 | E 2/2/0; N 3/3/1; T0 M2 L0 C0 |
| `cx_societate_068` | B5 | A6, B1, B2, B6 | E 1/1/0; N 4/4/2; T1 M1 L0 C0 |
| `cx_societate_151` | B5 | A6, B6 | E 2/2/0; N 1/1/0; T1 M2 L0 C0 |
| `cx_societate_152` | A6 | B2 | E 3/3/1; N 4/4/1; T1 M0 L0 C0 |
| `cx_societate_155` | B1 | A6, B2 | E 1/1/1; N 3/3/1; T2 M0 L0 C2 |
| `cx_societate_216` | A6 | B2, B6 | E 2/2/0; N 4/4/0; T2 M0 L0 C0 |
| `cx_societate_217` | A6 | B1, B2, B6, B9 | E 1/1/0; N 3/3/1; T2 M0 L1 C2 |
| `cx_societate_220` | A6 | B1, B6 | E 0/0/0; N 2/2/1; T0 M0 L0 C0 |
| `cx_societate_280` | A6 | B1, B2 | E 1/1/0; N 4/3/0; T1 M0 L0 C0 |
| `cx_societate_290` | A6 | B1, B2, B9 | E 0/0/0; N 3/3/0; T1 M0 L2 C0 |
| `cx_sport_072` | B6 | A6, B1, B2 | E 1/1/0; N 2/2/0; T1 M0 L0 C0 |
| `cx_sport_073` | A6 | B1, B6 | E 2/2/0; N 4/4/1; T0 M0 L0 C1 |
| `cx_sport_074` | B1 | A6, B2, B6, B9 | E 0/0/0; N 2/2/1; T2 M0 L1 C2 |
| `cx_sport_076` | B1 | A6, B2, B6, B9 | E 0/0/0; N 1/1/1; T2 M0 L3 C2 |
| `cx_sport_077` | B1 | A6, B2, B9 | E 0/0/0; N 2/2/0; T2 M0 L1 C0 |
| `cx_sport_156` | A6 | B1, B2, B6 | E 2/2/2; N 3/3/0; T2 M0 L0 C2 |
| `cx_sport_157` | B1 | A6, B2, B6, B9 | E 0/0/0; N 1/1/0; T1 M0 L2 C0 |
| `cx_sport_160` | A6 | B1, B2, B6 | E 1/1/1; N 4/4/1; T2 M0 L0 C2 |
| `cx_sport_161` | B5 | A6, B1, B2, B9 | E 2/2/0; N 2/1/0; T4 M1 L1 C0 |
| `cx_sport_222` | A6 | — | E 3/2/1; N 4/4/1; T2 M0 L0 C1 |
| `cx_sport_225` | A6 | B1, B2, B6 | E 1/1/1; N 2/2/0; T3 M0 L0 C1 |
| `cx_sport_226` | B1 | A3, A6 | E 1/0/0; N 1/1/0; T0 M0 L0 C0 |
| `cx_sport_282` | A6 | B1, B2, B9 | E 0/0/0; N 3/3/1; T3 M0 L2 C0 |
| `cx_sport_284` | B6 | A6, B1, B2, B3, B9 | E 0/0/0; N 2/2/0; T2 M0 L2 C1 |
| `cx_stiinta_083` | A1 | A6, B1, B2, B8 | E 1/1/0; N 3/3/0; T2 M0 L0 C0 |
| `cx_stiinta_162` | B5 | A6, B6 | E 2/2/0; N 4/4/1; T0 M2 L0 C1 |
| `cx_stiinta_165` | B1 | A6, B2, B9 | E 1/1/0; N 3/3/0; T2 M0 L0 C0 |
| `cx_stiinta_167` | A6 | B1, B2, B6 | E 2/2/0; N 2/2/1; T2 M0 L0 C2 |
| `cx_stiinta_227` | A6 | B1, B6 | E 1/1/0; N 2/2/1; T1 M0 L0 C2 |
| `cx_stiinta_285` | A6 | B1, B2, B5 | E 1/1/1; N 3/3/1; T1 M1 L0 C1 |
| `cx_viata_de_roman_238` | B1 | A6, B2, B6 | E 0/0/0; N 3/3/1; T2 M0 L0 C0 |

## Reproduction

```bash
PYTHONPATH=. /home/dobo/work/romania_scraper/.venv/bin/python \
  scripts/critique_pack.py --game conexiuni --status approved \
  --ids "$(python -c 'import json; print(",".join(json.load(open("cat_de_roman_esti/fixtures/board_demotions_v43.json"))["ids"]))')"
git diff --check
```
