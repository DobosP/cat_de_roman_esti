# 2026-07-26 — V42 design verdict (fun, quality, quantity, release)

Valid until: V42 landed on main (2026-07-29, `7e862b4`) — treat as history. Preserved
verbatim from the orchestrating session's working doc; the shipped form is ADR-0062..0065.

## The judge's diagnosis

The six games' mechanics are sound and well-engineered. The fun deficit has four causes, in
order of impact:

1. **Content quality variance in the served pool.** Rubric-killing boards were
   `pilot_eligible`: B5 mirror boards with play_quality 0–4 (cx_stiinta_162,
   cx_societate_067), generic-filler tiles ("Muzeu" among museums, "Politician" among
   funcții), B9 self-leak ("Pictura lui Nicolae Grigorescu" beside "Nicolae Grigorescu"),
   bland Alchimie targets ("Aperitiv"). Eligibility = zero deterministic FAIL, but B5/B6
   are WARN-level lints — judge-rubric failures passed through. The *worst served board
   defines the player's trust*, not the average.
2. **Thin shelves force repetition.** 4 Conexiuni categories had zero Ușor boards (hidden,
   so the menu shrank); Cald sau Rece istorie/muzica/sport at greu = 1 board each; Alchimie
   had 10 singleton category×difficulty combos and a category-daily `min_pool=1` that served
   the *same board every day forever*; Perechi limba/știința were 3-near-duplicate dead
   shelves; Intrusul limba had 1 preferred board. Meanwhile 222 pending items sat ungated
   (Lanț could nearly have doubled: 107 pending vs 94 approved — in the end its pending wave
   proved ~75% junk at the gate, so authored content carried quantity instead).
3. **Harsh loss states + stingy help.** 3/4 pairs solved → 0 points; Intrusul loss → 0; one
   clue gated behind burning half the mistake budget (Conexiuni, Perechi); Alchimie demanded
   3 fruitless combines before any nudge in a deliberately sparse space where "Nicio
   combinație nouă" was the dominant experience; Lanț normal/greu gave *zero* directional
   feedback and its 3-stage hint ladder reset on every move; Cald sau Rece read "Înghețat"
   for ~60% of guesses and explained ranks only in a desktop hover tooltip.
4. **No reason to return.** No streak, no daily-circuit reward, invisible progression
   (starter graduation undiscoverable), thin value proposition above the fold.

**What fun looks like here** (from direct board sampling): the best items produce
recognition-joy — "Pauza mare dulce" (ROM, Eugenia, Turbo, Lapte și corn), Ghencea → Finala
de la Sevilla, Petrache Poenaru → stiloul, țuica de casă din gospodăria bunicilor. The worst
were civics-exam content (norma Academiei, ÎCCJ) or graph exercises. **Authoring bar for
V42: "ai zâmbi când îl rezolvi?"** — solving should trigger "aha + haha",
prime-time-audience wide, cross-generational.

## Wave A — Content (fun lever #1, zero code risk)

A1. Gate all 222 pending items through critique-games (gate mode); orchestrator reviews
    every verdict + evidence before apply; apply via `apply_rereview.py` (fail-closed).
A2. Sweep served stock: eligible Conexiuni boards in the bottom play_quality band + all
    WARN-flagged eligible boards → sweep-mode proposals for Paul. Approved content is never
    auto-demoted (ADR-0019/0023).
A3. Author new content (orchestrator creates; fleet verifies; gate judges): Conexiuni Ușor
    × the four empty shelves (6–8 each so ≥4 survive; 8 = shared-daily floor); Conexiuni
    limba + știința (eligible sources for the derived dead shelves); Cald sau Rece greu
    fills for istorie/muzica/sport; Alchimie singleton-combo fills with targets that are
    discoveries, not categories (E4); Lanț fills after the pending wave; new KG nodes/edges
    allowed via import_candidates (factual verification required); lean pop: muzică, sport
    (Generația de Aur, Nadia, Sevilla '86), meme/net, viața de român, gastronomie
    regională distinctivă (A7-clean).
A4. Rebuild + validate: rank_games_pack → build_derived_catalog_v38 → validate_games_pack
    → validate_fixture → full pytest + frontend tests.

## Wave B — Playability (surgical, non-score; scoring formulas stay pinned per ADR-0054)

B1. Cald sau Rece feedback legibility: recalibrated temperature bands so the cold half
    differentiates; always-visible mobile legend for rank + temperature; fuzzy resolve
    confirmation for non-exact matches.
B2. Lanț guidance: extend the ADR-0046 directional cue to `normal` (greu stays
    instinct-only); persist hint-ladder progress across moves; intro explains corridor,
    undo, free typing, cap.
B3. Alchimie empathy: nudge unlock after 2 fruitless combines (was 3); bounded non-revealing
    whisper on repeated dead pairs; "Alt joc" action; category-daily min-pool floor 4 with
    fallback to the shared daily.
B4. Conexiuni help: second clue unlock at 3 mistakes (MAX_CLUES 1→2, same penalty mechanism
    — no formula change).
B5. Loss acknowledgment (display-only): Perechi/Intrusul loss screens state what was earned
    — scores unchanged pending pilot.
B6. Meta-loop: device-local daily streak derived from existing local history; full-circuit
    "Diplomă de român" stamp (text/CSS only); starter visibility chip + intro line;
    sharpened Home value-prop line.

Not in V42: score formula changes, 7th game (both wait for the anonymous pilot per ADR-0054
— this release IS the pilot vehicle), accounts (compliance checklist incomplete).

## Wave C — Release

Ship the anonymous arcade v1 (docker-compose.anon.yml, CAT_ACCOUNTS_ENABLED=0, no DB) with
V42. Pre-deploy gates: full backend+frontend suites, content validators, bundle ≤120 KiB,
manifest smoke. Owner decisions at release: CAT_LEGAL_OPERATOR + CAT_LEGAL_CONTACT_EMAIL
values, legal draft pages, and the deploy go itself. Rollback = redeploy the previous
checkout (V32 fixture artifact retained).
