# Task Result — Alchimie sparse recipes

## Summary

- Replaced live category-wide common-neighbour combines with a deterministic private
  target projection: one to four semantically ranked routes, at most 24 recipe pairs,
  32 projected concepts, and two required results per pair.
- Preserved every approved board's exact par, score penalties, target-id secrecy,
  category theme, fruitless-hint unlock, TTL 7,200 seconds, and 1,000-session cap.
- Added server-authored recent/useful/ready/depleted inventory state plus compact
  mobile-first `Recente` / `Utile` / `Toate` filters and ready-item highlights.
- Depleted concepts remain readable in the reaction journal but can no longer be selected;
  concise disabled labels explain that they were put aside.
- Made hints progressive: output label or public theme first, one useful owned pair later;
  private recipe ids, routes, and the hidden target id are never serialized pre-win.
- Superseded ADR-0013 with ADR-0044, updated the mobile contract and current STATUS.

## Projection audit

- Approved boards: 77/77 retain exact par; deterministic projection SHA-256
  `d1daaaab03a5af4d8ba797d38f8968eab24c7f04a154c4e155d86d708a26f4ef`.
- Routes: 72 boards expose 2–4; five graph-thin boards expose one.
- Recipes: 536 total; 459 singleton and 77 required two-result exceptions (85.6% single).
  A two-result recipe is accepted only when one selected route needs both together.
- Semantic quality: among the bounded discovered candidates, selected route minimum/median
  edge strength is 0.40/0.66. Only five mandatory shortest routes fall below the 0.55
  preference floor; weak extra routes fail.
- Openings: 61 boards expose at least two projected opening pairs; 16 expose one. The
  beginner UI marks currently ready ingredients instead of asking for blind search. A
  direct-builder sample of 12 mined boards had 7/3/2 boards with 2/3/4 live openings.
- Cold local measurement: all approved projections 10.670 s; 12 representative mixed mined
  sessions 17.842 s. Their shared-CI regression ceiling is a deliberately generous 45 s.

## Files changed

- `cat_de_roman_esti/wordgames/alchimie.py`
- `cat_de_roman_esti/wordgames/packs.py`
- `cat_de_roman_esti/wordgames/service.py`
- `scripts/import_candidates.py`
- `frontend/src/api/alchimie.ts`
- `frontend/src/screens/Alchimie.tsx`
- `frontend/src/styles/arcade.css`
- `frontend/tests/alchimie-lineage.test.mjs`
- `frontend/tests/alchimie-projection.test.mjs`
- `tests/test_alchimie_sparse_recipes.py`
- `tests/test_wordgames_alchimie.py`
- `tests/test_alchimie_scoping.py`
- `tests/test_mobile_contract.py`
- `docs/adr/0013-alchimie-category-scoped-combines.md`
- `docs/adr/0044-alchimie-sparse-recipe-projection.md`
- `docs/MOBILE_CONTRACT.md`
- `docs/STATUS.md`

No generated `cat_de_roman_esti/web/static` artifact or dependency symlink remains.

## Verification

- Alchimie + scoping + sparse projection + mobile contract + session store: 60/60 passed.
- Full backend: 396/396 passed; collection confirms five new sparse-recipe tests.
- `ruff check --no-cache .`: passed.
- `validate_games_pack.py`: GREEN.
- `validate_fixture.py`: GREEN.
- `node --check .claude/workflows/critique-games.js`: passed.
- Frontend `npm test`: 10/10 passed; `npm run typecheck`: passed; `npm run lint`: passed.
- The pre-review production build passed at 116.20 KiB gzip / 120 KiB. Per final dispatch,
  static was not regenerated after the depleted-journal source fix; combined integration
  must run the final build/bundle gate.
- `git diff --check`: passed.

## Risks / manual review

- Five approved boards have only one viable selected route and 16 curated boards only one
  projected opening pair. They remain exact-par solvable and visually expose ready
  ingredients, but deserve a Romanian beginner playtest before public rollout.
- Route strength is a legibility proxy, not human judgment. The five mandatory below-floor
  paths should be first in a future authored-recipe review queue. State/candidate ceilings
  and one deterministic parent per convergent state mean this is not a global optimum proof.
- Root must reconcile shared STATUS/mobile-contract edits with the parallel Contexto and
  Lanț branches and produce the single combined tracked static bundle.

## Merge recommendation

Green and recommended for integration. Do not commit this `TASK_RESULT.md`; no commit,
merge, push, deploy, or worktree deletion was performed here.
