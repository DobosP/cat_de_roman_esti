# V43 release board rebuild review

_Reviewed and closed 2026-07-30. This report records the evidence for ADR-0067._

## Scope and release standard

The review replayed the recently landed Fable 5 content workflow instead of treating its
verdicts as ground truth. It covered every one of the 67 owner-demoted Conexiuni boards,
all 268 groups inside them, every new authored candidate, the full approved + pending
inventory, both KG mirrors, the ranking and derived-catalog contracts, and direct
Intrusul/Perechi creation paths.

The release bar was unanimity, not shelf fill:

1. exact deterministic preflight against approved, reserve, pending, and rejected stock;
2. independent factual review of the exact candidate bytes;
3. independent blind play-quality review of the same bytes;
4. a second exact-dossier analyst/verifier pair after import under real IDs;
5. final playability, artifact, API, and full-suite gates.

A candidate with a true but ambiguous second group, a vague association bundle, an
obscurity-based difficulty spike, or a stale fact was rejected even when the structural
lint was green. Empty shelves remain hidden safely; no board was forced through to meet a
quota.

## What the replay found

The landed workflow had useful deterministic and adversarial layers, but four gaps let
weak content look finished:

- It sampled survivors more deeply than demotions. Rejected ideas therefore remained
  available for later one-tile reskins.
- It measured eligible stock more often than the full pack. Pending and reserve boards
  still carry freshness debt even when they are never selected at runtime.
- It recognized exact quads and several graph conflicts but not enough literal predicates,
  displayed-name ambiguities, type worksheets, or vague “things associated with X”
  constructions.
- Human reviews were not uniformly bound to the exact candidate, KG, rubric, full ID set,
  and complete coverage. A fact correction could make an earlier judgment stale without an
  obvious failure.

Those were material gaps. The first 66 author proposals (30 cultural, 36 everyday) became
44 early survivors and were imported as pending IDs `316..359`. After correcting source
facts and regenerating exact dossiers, only three were unanimously promotable at that
gate:
`cx_personalitati_339`, `cx_sport_355`, and `cx_stiinta_356`. The other 41 boards were
removed, and their 164 groups are now durable rejection tombstones.

## Demotion audit and reusable patterns

All 67 ADR-0066 boards remain demoted, and all 268 original quads are hard-banned for
direct reuse. The exact historical census is
[v43-demotion-pattern-audit.md](v43-demotion-pattern-audit.md).

The dominant patterns were:

- **Freshness debt:** 211/268 demoted groups had an exact or 3-of-4 collision in the full
  pack; runtime-only counting hid most of it.
- **Association bundles:** people, works, events, institutions, and places were gathered
  around a theme without one sentence that applied identically to all four.
- **Visible construction:** class + instances, four homogeneous node types, and labels
  containing a tile supplied the answer rather than a fair clue.
- **Mirrors:** inventors↔inventions, festivals↔hosts, universities↔cities, and
  rulers↔events produced alternative partitions or answer keys.
- **Recognition inversion:** several “easy” boards depended on multiple specialist names;
  difficulty came from obscurity instead of the relationship.
- **Fact drift:** current programmes, transfers, public systems, and rollout dates had
  changed after the source graph was written.

Four predicate ideas remain usable only as ideas: Romanian UNESCO heritage, the “mare”
word family, anti-communist opposition, and familiar sport nicknames. Any derived group
must change at least two members, sit beside three fresh groups, and pass the full current
gate. The original quads stay banned.

## Workflow changes

The V43 gate now:

- compares candidates with the full pack and durable rejection tombstones for exact,
  3-of-4, and at-least-8-of-16 reskins;
- checks projected approved use above eight, class/container structures, mirror pairs,
  normalized label leaks, four-type answer keys, and three-type shortcuts;
- parses visible prefixes, suffixes, contained words, years/digits, initials, first-name
  length, surname initials, and displayed word counts, then rejects foreign tiles that
  also satisfy the surface rule;
- blocks recurring vague predicates such as “țin de”, “repere ale”, “apar în”, “fac parte
  din”, “lumea”, “constelația”, and unconstrained association language;
- binds every review to exact candidate bytes, KG digest, rubric digest, requested IDs,
  and complete one-row-per-item coverage;
- records both real-ID judgments and promotes only on two explicit `promote` verdicts;
  disagreements synthesize the more conservative `keep` or `reject` result;
- retains rejected groups transactionally with per-board, per-group, and source-gate
  digests; rollback restores the tombstone file together with both pack mirrors;
- makes the saved audit, author-verification, and critique workflows inspect rejected
  evidence rather than only promoted content.

The focused contract suite covers exact/near/reskin rejection, surface and type severity,
tamper detection, full coverage, and transactional rollback.

## Strict approved-stock cleanup

The strict approved-stock sweep exposed six more approved boards that were not safe to
select, and the final real-ID re-audit exposed two early-wave incumbents. ADR-0067 adds
all eight to the reserve-demotion sidecar:

| Board | Release blocker |
|---|---|
| `cx_geografie_024` | `București` repeats its own group label and acts as the container for three co-members; deterministic fairness also flags Banat, Băile Herculane, and Muntenia, and two other groups repeat approved stock. |
| `cx_geografie_304` | Sulina and Tulcea also satisfy the Danube-port predicate, breaking the Delta partition. |
| `cx_limba_260` | `Școala Ardeleană` repeats its own answer; two groups mix work/person or work/concept types, and two groups are exact/near repeats of approved stock. |
| `cx_muzica_138` | Festival↔host-city mirror; [`Sub pielea mea` also satisfies the international-hit predicate](https://snepmusique.com/pdf/classement_pdf.php?annee=2016&categorie=yacast&semaine=36&type=simple); the frozen Constanța record no longer matches [current organizer location material](https://neversea.com/info/67744b91-5516-4769-b3f7-c27a144a1fd6). |
| `cx_societate_066` | Universities mirror cities, while the remaining labels are type sorting or broad cultural association. |
| `cx_stiinta_080` | Four inventors mirror four inventions; “Sonicitate” also fits the supposed fields group. |
| `cx_personalitati_339` | Three displayed-name worksheets leave the 1848 group by elimination; four Romanian football internationals form a clean cross-group guess. |
| `cx_sport_355` | Initial/year worksheets sit beside a four-tile EURO 2024 association and an over-entangled Olympic-medalist field. |

The last two emerged when the fresh real-ID critics re-audited the three early-wave
incumbents beside the final replacements; both critics agreed to demote them and to keep
`cx_stiinta_356`. All eight stay approved reserves so frozen-derived source invariants
remain valid, but ranking selection excludes them. The sidecar now contains 75
owner-demoted boards.

## Replacement funnel

The first replacement passes confirmed why generation is not approval:

- the first 20 deterministic-clean cultural reconstructions received 0 keep / 20 rebuild
  in a blind design audit;
- the next cultural pass was narrowed again after freshness, overuse, and fairness
  failures;
- the reduced cultural pool then exposed a `Maitreyi` eponymous-title crossfit, a weak
  society association board, a flat taxonomy worksheet, and the displayed-title
  ambiguity of `Pasărea măiastră`;
- the first 21 everyday finalists produced only 8 factual keeps and 7 independent quality
  keeps. Reviewers caught pumpkin↔pie filling, Drobeta compound-toponym, Suceava
  river/county ambiguity, Olympic category overlaps, a false Ponor world-title claim,
  class/instance mixing, and a giant-bacterium exception to an absolute naked-eye label.

Authors combined sound groups, replaced ambiguous members, sharpened predicates, retiered
or held weak boards, and reran the full inventory preflight. The final raw-review pools
were deliberately small: two cultural proposals from 20 slots and nine everyday
proposals from 21, with 30 explicit holds before the last independent reviews. Fresh
quality review then dropped both remaining cultural proposals: the art board was a
school-program worksheet/leftovers solve, and the film board missed its easy tier while
repeating three familiar shelf concepts from approved stock. No cultural board was
imported merely to fill those shelves.

The everyday exact-byte reviews returned five factual-clean boards versus four blocked
crossfits, and three quality keeps versus six drops. Their intersection contained only
`v43r_personalitati_normal_02` and `v43r_sport_normal_03`, imported temporarily as
`cx_personalitati_360` and `cx_sport_361`. Fresh real-ID critics rejected both: the first
had a clean presenter/chef MasterChef alternative quartet, while the second combined an
ambiguous Gică/Gheorghe first-name rule with repeated Olympic résumé sorting. The gate
also unanimously moved `cx_personalitati_339` and `cx_sport_355` to reserves and retained
`cx_stiinta_356`. Thus the strict rebuild added no new selected board; one early-wave
science board is the sole selected survivor. Exact candidate bindings and both critic
outcomes are in [the funnel manifest](v43-release-funnel.json), and the applied schema-v2
decision is [the final gate artifact](v43-final-gate/conexiuni_verdicts.json).

## Verified source corrections

The two KG mirrors now agree on these source-backed corrections:

- Radu Drăgușin's July 2026 Fiorentina loan;
- the 5 February 2024 `Power Couple România` premiere and Dani Oțil's role from 2024;
- the 17 March 2012 `Te cunosc de undeva!` launch;
- historical CEI wording that bounds the PNRR-supported first-card cost through
  30 June 2026;
- e-SIGUR as the operational Police system using visible mobile tripod devices, distinct
  from the later integration of monitoring systems operated by road administrators,
  including CNAIR;
- Aurelia Dobre's durable TikTok description without a scope-dependent “most followed”
  superlative or a fast-expiring exact follower count.

The false e-SIGUR↔rovinieta and e-SIGUR↔A7 edges were removed. The KG remains 2,364 nodes
and 180 puzzles, with 9,217 edges.

Sources: [Tottenham Hotspur](https://www.tottenhamhotspur.com/news/1076954/dragusin-joins-fiorentina),
[Antena 1 — Power Couple](https://a1.ro/power-couple/stiri/cand-are-loc-premiera-power-couple-romania-la-bine-si-la-greu-showul-care-redefineste-relatia-de-cuplu-incepe-din-5-februarie-id1107983.html),
[Antena 1 — Te cunosc de undeva](https://a1.ro/tv/stiri-tv/vedete-una-si-una-in-cel-mai-nou-show-al-antenei-1-ei-sunt-concurentii-super-show-ului-te-cunosc-de-undeva-id11869.html),
[CEI official information](https://carteadeidentitate.gov.ro/utile/),
[Poliția Română — e-SIGUR](https://politiaromana.ro/ro/stiri/primele-dosare-penale-pentru-fals-in-declaratii-deschise-in-cazuri-semnalate-de-sistemul-e-sigur),
[MAI's CNAIR integration distinction](https://www.mai.gov.ro/declaratie-de-presa-lansarea-proiectului-siguranta-in-trafic/),
and [Pro TV's conflicting current TikTok superlative](https://www.protv.ro/articol/119695-andra-gogan-cea-mai-urmarita-romanca-de-pe-tiktok-video-viral-alaturi-de-shakira-fanii-au-ramas-fara-cuvinte-nu-pot-sa-cred-ca-ai-cantat-cu-ea).

## Intrusul and Perechi release integrity

Changing the source pack without rebuilding the digest-bound derived catalog reproduced
the reported failure: create-game raised an uncaught source-drift `ValueError` and
returned 500. Both games now translate unreadable or invalid derived artifacts to a
stable Romanian 503 response, including seeded and daily Perechi paths. Rankings and both
catalog copies were then regenerated, and the pinned catalog digest was restamped.

The complete `boards` array stayed byte-for-byte identical: SHA-256
`71a2acefb7e0ec62da32ad2645238d73d5e83375808160c0bd1800febd3a73b6`,
336 entries (183 Intrusul, 153 Perechi). Only the four source-binding metadata digests
changed. Direct Intrusul and Perechi create-to-win tests now return 200 again; corrupt or
unreadable catalogs remain covered by stable 503 tests.

## Closure census

- Pack: 828 records = 606 approved + 222 pending; Conexiuni is 311 = 232 + 79.
- Ranked runtime: 448 zero-FAIL records, including 74 Conexiuni; ten empty Conexiuni
  shelves remain safely hidden.
- Reserve/rejection debt: 75 owner-demoted IDs and 43 rejected-board tombstones covering
  172 groups.
- KG: 2,364 nodes / 9,217 edges / 7,440 aliases / 180 puzzles.
- Frozen derived catalog: 336 boards = 183 Intrusul + 153 Perechi, with unchanged board
  payload and regenerated source bindings.
- Release gates: backend 679/679, accounts 53/53, session store 16/16, frontend 152/152,
  Ruff/ESLint/typecheck, 118.03/120 KiB production bundle, artifact validators, and
  whitespace all green.
