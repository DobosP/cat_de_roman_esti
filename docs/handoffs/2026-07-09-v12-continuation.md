# Handoff — v12 quality consolidation → v12.1 content fixes

Valid until: the v12.1 content-fix batch below is applied — then treat as history.

Written 2026-07-09 (Linux, Claude Code, ultracode). v12 (structural consolidation) LANDED on `main`
(see `git log` for the `feat(v12)` commit). This handoff carries the DEFERRED content fixes v12 did not
apply, plus the method to resume.

## What v12 did (landed)

A two-fleet Codex pipeline, then a purely-structural apply (status/existence only, no content authoring):

1. **Audit** — 56 workers (one per game×category) judged all 865 games on a *resolved* view (node ids
   pre-expanded to `label_ro — description`, so Codex saw real Romanian content, not opaque ids). 408 flagged.
2. **Adversarial verify** — 53 workers independently re-checked the 249 highest-stakes verdicts with a
   **defender bias on served/approved content** and a **skeptic bias on promotes**. This overturned **35%**
   of first-pass flags as false positives — the load-bearing step (the first pass confidently mis-flagged
   correct boards, e.g. "Ioni de manual" containing I.L. = _Ion_ Luca Caragiale).
3. **Exact-dedup scan** — mechanical, cross-category (the per-slice workers can't see it).
4. **Apply** — `−101 remove` (92 exact duplicates + 9 verified-broken approved boards), `−29 demote`
   (approved→pending, off-theme), `+86 promote` (verified). Pack **865 → 764 (638 approved / 126 pending)**.

Dominant defect found: **Contexto same-target duplicates** — 78 removed (no two served Contexto games now
share a hidden answer). Every category retains ≥3 approved boards per game.

Full machine-readable decision record (all 360 actions incl. the deferred ones, with reasons):
`docs/handoffs/2026-07-09-v12-actions.json` (fields: id, game, from_status, action, to_status, source, reason, detail).

## Test situation (important)

v12 is a **pure data change** to both `games_pack.json` copies. Validated by the authoritative stdlib gates:
`validate_games_pack.py` (GREEN — full playability of every approved item via the *same* `wordgames.packs` /
`WordGameService` functions the server serves with) and `validate_fixture.py` (GREEN — KG untouched), plus
the 81 stdlib pytest. **The Django/DRF web-layer suite (test_web / test_wordgames_* / test_wordgames_curated)
did NOT run locally** — neither the `romania_scraper` venv nor any fleet venv has Django, and pip can't
bootstrap on this host. Those tests exercise HTTP plumbing that v12 did not touch; they run in CI on push.
Before pushing, run the full suite in a Django venv (`pip install -c constraints.txt ".[web]" pytest`).

## v12.1 — deferred content fixes (verified, not yet applied)

These need content authoring and/or KG edits + re-derivation, so they were held out of the structural pass.
Each was **upheld by the adversarial verifier** unless marked from a `modify` call.

### Systemic finding: KG labels were ASCII-folded (missing diacritics) — ✅ DONE (v12.1, 2026-07-09)
Several "fixes" were the same root defect — node `label_ro` values stored without diacritics. RESOLVED by a
16-worker Codex diacritics fleet: **134 labels** restored in both `kg_sample.json` copies (`Ion Creangă`,
`Ștefan cel Mare`, `Nadia Comăneci`, `Lacul Roșu`, `Munții Apuseni`, `Țara Românească`, `România`…), each gated
by the invariant `normalize(new)==normalize(old)` so `alias_unique`/resolver are provably unaffected (both key
on the accent-stripped form). Mobile snapshot regenerated; mirrored into `dense_data.json`/`expansion_data.json`.
**Because boards reference node ids (display resolves `label_ro` at runtime), this auto-fixed the diacritics-class
game "fixes"** below (e.g. `ct_geografie_030/031/033/137` targets, `cx_viata_de_roman_089/173`, `cx_meme_net_204`).
Method: `scripts` in the session scratchpad (`prep_diacritics.py` / `apply_diacritics.py`) — regenerable.

### Fixes status (updated 2026-07-10)
DONE: ~10 diacritics-class (auto-fixed by the KG pass), **17 difficulty-tier recalibrations** (applied +
revalidated green), **2 member-swaps** whose replacement node already existed (`cx_istorie_034` Anghel
Saligny→Elie Carafoli, `cx_societate_068` Avocatul Poporului→Drepturi civile), **2 group-label rewrites**
(`cx_gastronomie_018`, `cx_literatura_042`).
DONE 2026-07-10 (tail closed): created 6 leaf-connected KG nodes and applied the swaps that needed them —
`cx_geografie_109` (Mila 23 / Crișan), `cx_istorie_181` (Imperiul Țarist), `cx_muzica_273` (Ducu Bertzi),
`cx_istorie_115` (Colonizarea romană), `cx_istorie_118` (Procesul Ceaușescu). Also 4 node desc/label fixes +
4 promote-after-fix (`ct_limba_149`, `ct_literatura_228`, `lt_geografie_168`, `ct_societate_088`).
INTENTIONALLY SKIPPED: `cx_gastronomie_172` (swap → generic "Emisiune TV" weakens the board — left as-is);
`ct_film_tv_018` node-category (Cristian Mungiu personalitati↔film_tv is genuinely dual, and node-category
changes are cross-cutting — not worth the churn). **v12.1 is complete; this handoff is now history.**

<!-- BEGIN fixes table -->
(see 2026-07-09-v12-actions.json; representative rows)
- `cx_istorie_034` swap member Anghel Saligny → Elie Carafoli (Saligny is a bridge engineer, not aviation)
- `cx_muzica_273` swap member "Vers" → Ducu Bertzi (Vers is a literary term, not a folk act)
- `cx_geografie_109` swap g3 "Delta Dunării"/"Sfântu Gheorghe (braț)" → "Mila 23"/"Crișan" (avoid double-membership)
- `ct_geografie_030/031/033/137` target label diacritics: Lacul Roșu, Peștera Scărișoara, Munții Apuseni, Podișul Transilvaniei
- 17× difficulty tier moves (al_istorie_001, ct_istorie_042, lt_societate_153, …)
<!-- END fixes table -->

### 15 modify calls — partially DONE (2026-07-10)
DONE: the 4 "reject not promote" calls (`cx_geografie_176`, `cx_limba_191`, `cx_meme_net_135`, `lt_film_tv_162`)
were removed from the pending pool; the diacritics-class ones (`cx_meme_net_137` Nadia Comăneci, `cx_viata_de_roman_169`
Amintiri din copilărie) were auto-fixed by the KG pass and their "do NOT demote" is honoured (they stay approved).
STILL DEFERRED: `cx_istorie_115/118` (member swaps needing new nodes — see above); `lt_geografie_024` — keep
approved, fix its node description copy; `ct_limba_149`/`ct_literatura_228`/`lt_geografie_168`/`ct_societate_088`
— promote *after* a small clue/label fix. Full text in the actions JSON.

### Low-stakes, regenerable
- **22 audit-only pending rejects** (Conexiuni boards the audit disliked; not adversarially re-checked because
  pending = not served). Left as pending review inventory. To action: build `<game>_verdicts.json` and run
  `scripts/apply_rereview.py`.
- **42 pending fixes** and the remaining pending pool — normal review backlog.

## How to resume v12.1
The two Codex fleets are reproducible (scratchpad outputs are session-local — regenerate, don't hunt for them):
the audit sliced the pack by game×category into self-contained resolved briefs, fanned out via a Sonnet-relay
→ `codex-run.sh --schema` workflow; the verifier did the same over the flagged subset with defend/skeptic briefs.
But you don't need to re-run them — `2026-07-09-v12-actions.json` already holds every verified decision. For the
content fixes, apply the diacritics KG pass first (biggest leverage), then the swaps/tier moves, then re-gate.
