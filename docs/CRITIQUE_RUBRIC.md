# Content critique rubric (ADR-0023)

Hard-critique standard every curated pack item must pass **before** `status: approved`.
Two layers: deterministic lints (`scripts/critique_pack.py`) and an LLM judge fleet
(`.claude/workflows/critique-games.js`) applying this rubric with live web checks.
The playability validator (`scripts/validate_games_pack.py`) checks *solvability*;
this rubric checks whether the item is **fair, recognizable, and fun for a broad
Romanian audience**. ADR-0019's editorial boundary sits ABOVE this rubric: a judge
verdict never overrides it.

Verdict vocabulary (durable contract, consumed by `scripts/apply_rereview.py`):
`{"game": "<kind>", "verdicts": {"<item_id>": "promote|reject|keep"}}` for pending
items. Sweeps over `approved` items output *proposals* (`keep|demote|revise`) for the
owner — approved content is never auto-demoted.

## A. Universal kill criteria (all four games)

- **A1 Recognition floor.** The concepts a player must produce or recognize are things
  an average Romanian (non-specialist, cross-generational) has actually heard of.
  Operational test: would it be unremarkable in a prime-time TV quiz? Judges verify
  doubtful cases on the web (see D). One deliberate deep-cut per item is allowed on
  `greu` only, and only when the rest of the item carries it.
- **A2 Social relevance.** The item's theme is something Romanians actively think or
  talk about (school canon, national media, charts, living memory, current internet
  culture) — not a concept that merely *exists* and is technically Romanian.
  "It makes sense but nobody would ever think of it" = kill.
- **A3 Predicate honesty.** Labels and descriptions promise exactly what the content
  delivers. No word-salad labels enumerating unlike things ("Festival, mare, castel,
  sat"), no vibe-only themes.
- **A4 Factual verifiability.** Any claim embedded in the item (who wrote what, where
  something is) must be web-verifiable. Unverifiable → reject (same rule as the
  v18-v21 import rail).
- **A5 ADR-0019 boundary.** Adult framing, profanity, alcohol-dependent play value,
  insensitive historical humor, near-duplicate of a served board: in GATE mode →
  `keep` (stays pending) regardless of quality scores — the owner decides. In SWEEP
  mode every verdict is already only an owner proposal: return your honest quality
  verdict and flag the A5 trigger in the reasoning — never convert a quality kill
  into `keep` out of deference (that hides the signal the owner needs).
- **A6 Freshness.** Not a re-skin of an already-approved item (same mechanic + same
  concepts under a new label). Lint `duplicate_groups` / shared-member counts are the
  signal; the judge decides if the overlap is a re-skin.

## B. Conexiuni boards (4 groups × 4 tiles, labels hidden until solved, 4 mistakes)

Grounding: NYT Connections editorial practice (difficulty gradient; overlap as a
*designed* trap), Koster's red-herring budget rule, MCQ single-best-answer standards.

- **B1 Strict predicate per group.** Every member satisfies the group label as a
  checkable predicate of the SAME relation type. "Festivals" may contain only
  festivals — never the village that hosts one (cx_meme_net_136's Untold/Neversea/
  Electric Castle + **Bonțida** is the canonical failure). Mixing "is an X" with
  "is associated with X" members in one group = kill (Predicate Inconsistency).
- **B2 Type discipline.** A group mixing KG `node_type`s (3+1 outlier, or 2+2 split)
  is presumed broken unless the label explicitly names a type-agnostic predicate that
  every member still strictly satisfies (e.g. "Au Paris în biografie" over persons is
  fine; person+work mixes almost never are). Lint: `type_coherence`.
- **B3 Unique partition.** Exactly one defensible 4×4×4×4 partition of the 16 tiles.
  A tile that fits two groups' predicates equally well = kill. Lint `tile_fairness`
  (FAIL) fires when a tile has more on-board KG neighbors in a *type-compatible*
  foreign group (one holding ≥2 members of the tile's node_type) than in its own.
  The raw engine rule (`_board_quality`: any foreign group counts) is reported in the
  dossier as `fairness.engine_unfair_raw` — judges MUST read it: a board that passes
  `tile_fairness` but has a high raw count is thematically tangled and needs the B1–B5
  walk with extra suspicion.
- **B4 Red-herring budget.** Deliberate traps are the craft — but plausible-but-wrong
  placements must number FEWER than the 4-mistake budget (Koster's rule), and each
  must resolve uniquely once spotted. Lint: `red_herring_budget` on contested tiles.
- **B5 No mirrored groups.** Two groups in ≥3-way 1:1 strong correspondence
  (festivals ↔ their host cities; hosts ↔ their own shows; inventors ↔ their machines)
  make label-guessing a coin flip and read as lazy authoring. One crossing pair is a
  trap; three is a mirror. Lint: `mirrored_groups`.
- **B6 No generic-filler groups.** A group of bare dictionary abstractions
  ("Concert, Festival, Spectacol, Public") is not puzzle content, and its members act
  as archetype-magnets for other groups' proper nouns. Kill.
- **B7 Difficulty gradient.** Board has one anchor group an average player secures
  fast, and the hardest group uses a *nameable* trick (double meaning, shared name,
  hidden pattern, franchise), not just obscurity. No tier inversion: nothing in an
  `usor` board should demand rarer knowledge than a `greu` tile.
- **B8 Recognition per group.** ≥3 of 4 members pass A1 on their own; at most one
  deep-cut per group, and only on normal/greu.
- **B9 Label self-leakage.** A group label must not contain a member's name, and must
  not be trivially reverse-engineerable from a single member alone.

## C. Contexto / Cald sau Rece targets (guess-by-association, rank feedback)

Grounding: Contexto.me curates common concrete nouns and excludes isolated
embeddings; Semantle's uncurated pool is the cautionary tale.

- **C1 Nameable-thing test.** The target is a concrete, spontaneously nameable thing
  (person, place, dish, work, event, object). Abstract categories, records,
  meta-concepts and "image-symbols" (Sonicitate, Pagaia din Deltă,
  Recensământul populației) = kill: nobody free-associates their way to them.
- **C2 Recognition ≥ band.** `usor` targets: universally known (school canon or
  prime-time fame). `normal`: broadly known. `greu`: still A1-recognizable — ONLY the
  associative path may get harder, never the fame. An unknown target is not "hard",
  it is unfair (Semantle failure).
- **C3 Dense, legible neighborhood.** ≥5 direct KG neighbors that are themselves
  recognizable, so early guesses give a gradient (engine floors: reachable ≥120,
  responsive ≥40 — necessary but not sufficient).
- **C4 Obvious opener exists.** At least one guess a naive player would try early
  (the category's most famous concept) must land warm (≤2 hops).
- **C5 No polysemy.** Target label has one dominant sense for Romanians.
- **C6 Salience banding.** Lint `salience_floor` (WARN): usor <0.60, normal <0.35,
  greu <0.20 — a flag for judge review, not an auto-kill (KG salience under-rates
  some famous nodes, e.g. Insulina 0.25).

## D. Romanian-relevance web checks (judge protocol, doubtful cases)

A verifier with web access confirms A1/A2/C2 by checking ≥2 independent signals:
1. **ro.wikipedia.org** article exists with non-trivial content; pageviews not a
   single-event spike.
2. **School canon**: appears in programa școlară / manuale (edu.ro, manuale.edu.ro)
   for limba română, istorie, geografie.
3. **National media**: hits in digi24 / HotNews / ProTV / Libertatea / GSP within the
   last 5 years (site-restricted search).
4. **Charts/broadcast**: Romanian radio/TV chart or festival-lineup presence (music),
   box office / audience data (film/TV).
5. **Trends**: sustained (multi-year, not one spike) Google Trends RO interest.
6. **Cross-generational test** ("ar ști-o și mama"): documented presence both pre-2010
   and current. Single-cohort or single-subculture legibility → fails A2 for usor/normal.

## E. Judge-fleet protocol (fleet skill routing)

1. **Dossier**: `scripts/critique_pack.py --dossier <dir>` emits one JSON per item
   (members, node types, salience, descriptions, cross-group strong edges, lint flags).
2. **Critique** (analyst / Sonnet): per item, walk B or C above, simulate a player,
   name failure modes, propose a verdict + which claims need web verification.
3. **Adversarial verify** (Opus, web access): refute-first — try to overturn the
   critique; run section-D checks on every A1/A2/C2 claim; settle the verdict.
   Escalation, not majority vote, on disagreement (fleet skill rule 2).
4. **Apply**: pending items → `apply_rereview.py` verdict files; approved items →
   proposal list for the owner. Verdict archives stay in the session scratchpad
   (v16 precedent); the *contract* above is durable.

## F. Lint reference (`scripts/critique_pack.py`)

| Check | Games | Level | Meaning |
|---|---|---|---|
| `tile_fairness` | conexiuni | FAIL | tile has more on-board neighbors in a *type-compatible* foreign group (≥2 members of its node_type) than its own; raw engine count (`_board_quality` parity) ships in the dossier as `engine_unfair_raw` |
| `red_herring_budget` | conexiuni | WARN ≥2, FAIL ≥4 | contested tiles (foreign pull == own pull > 0) |
| `mirrored_groups` | conexiuni | WARN | group pair with ≥3 disjoint strong (≥0.6) cross edges |
| `type_coherence` | conexiuni | WARN | 3+1 type outlier or 2+2 type split in a group |
| `duplicate_groups` | conexiuni | FAIL (new) / WARN (stock) | exact 4-member quad already in an approved board; near-duplicate (3 shared members with an approved quad) always WARN |
| `salience_floor` | contexto, lant, alchimie | WARN | target/endpoint salience below difficulty band (C6) |
| `member_overuse` | pack-wide | WARN | node appears in >8 approved conexiuni boards |

FAIL blocks promotion (`--strict` exits 1). WARN routes the item to the judge fleet —
it may pass with justification recorded in the verdict reasoning.
