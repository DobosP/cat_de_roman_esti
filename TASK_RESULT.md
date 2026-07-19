# Task result — V38 mobile six-game interface

## Summary

- Added lazy Intrusul and Perechi routes, typed API clients, mobile-first tap boards,
  resume/replay fatigue, beginner starter selection, shared dailies, earned hints, and
  terminal-only server scores/shares.
- Expanded the lobby and health metadata to six games in the requested order; only
  Alchimie remains featured.
- Made six-game ranking navigation phone-safe with a native selector while retaining
  desktop tabs.
- Added privacy, OpenAPI, router/deep-link, beginner UI, responsive layout, and bundle
  coverage. Regenerated the tracked Vite release bundle.

## Files changed

- Frontend registry/router/lobby/ranking: `frontend/src/games.ts`, `App.tsx`, `Home.tsx`,
  `Ranking.tsx`, and `api/meta.ts`.
- New games: `frontend/src/api/{intrusul,perechi}.ts`,
  `frontend/src/screens/{Intrusul,Perechi}.tsx`, and
  `frontend/src/styles/{intrusul,perechi}.css`.
- Contracts/tests: `cat_de_roman_esti/web/meta.py`, `tests/test_web.py`,
  `tests/test_mobile_contract.py`, and focused frontend tests.
- Production assets: `cat_de_roman_esti/web/static/` including the Vite manifest.

## Commands and exact results

- `npm test`: **78/78 passed**.
- `npm run lint`: green.
- `npm run typecheck`: green.
- `npm run build`: green; 468 modules, **117.58/120.00 KiB** initial JS/CSS gzip,
  four Romanian font subsets; Intrusul/Perechi JS and CSS remain lazy chunks.
- Targeted final Django/static/mobile/game pytest gate: **59/59 passed**.
- Required `tests/test_wordgames_session_store.py`: **16/16 passed** (one expected
  warning because the lightweight venv does not load pytest-django).
- Targeted Ruff: green.
- `git diff --cached --check` before commit: green.

## Risks / manual review

- No automated visual browser runner is installed. A physical-phone pass below 340 px,
  at ordinary phone width, and at desktop width is still useful for copy wrapping.
- The initial bundle has 2.42 KiB gzip headroom; retain lazy game-specific imports.
- Account-backed ranking is generic by game key and was not changed; the new frontend
  keys flow through the existing score-sync path.

## Merge recommendation

Cherry-pick commit `16afc130a91a8d1f5ef9a8c56e4e2edc19d53c8f` onto the V38 integration
branch, then run the integration branch's full backend/documentation gate.
