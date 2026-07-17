# Task Result

## Summary

- Added a shared semantic three-step beginner guide and contextual `ACUM` cue.
- Defaulted all four game option screens to `Ușor` and shortened lobby/intro copy.
- Reworked mobile hierarchy: 44 px controls, single-row scrollable HUD/category rails,
  sticky Alchimie/Conexiuni primary controls, responsive Conexiuni tiles, scrollable Lanț
  breadcrumbs, visible Contexto rank meaning, polite status feedback, and safe shortcuts.
- Kept desktop focused at 760 px and refreshed the tracked Vite release output.
- Documented the decision in ADR-0031 and updated `docs/STATUS.md`.

## Files changed

- Shared frontend: `GameIntro.tsx`, `GameShell.tsx`, `Hud.tsx`, `CategoryPicker.tsx`,
  new `PlayGuide.tsx`, and `arcade.css`.
- Product surfaces: `Home.tsx`, `games.ts`, and all four game screens.
- Regression coverage: new `frontend/tests/mobile-beginner-ui.test.mjs`.
- Release/docs: tracked `cat_de_roman_esti/web/static/` bundle, `docs/STATUS.md`, and
  `docs/adr/0031-mobile-first-beginner-guidance.md`.

## Verification

- `npm run lint` — exit 0.
- `npm run typecheck` — exit 0.
- `npm test` — 31/31 passed.
- `npm run build` — exit 0; initial JS/CSS 116.11 KiB gzip / 120 KiB limit; four
  Romanian font subsets only.
- `PYTHONPATH=. /home/dobo/work/romania_scraper/.venv/bin/python -m pytest tests/test_wordgames_session_store.py -q`
  — 11/11 passed.
- `PYTHONPATH=. /home/dobo/work/cat_de_roman_esti/.venv/bin/python -m pytest -q`
  — full 324-test backend suite passed.
- Ruff, both fixture/pack validators, workflow syntax, and `git diff --check` — green.
- Manual/headless review: four intros at 390 px, smallest-phone stress at 320 px,
  desktop lobby at 1280 px, and active 390 px Alchimie + Conexiuni flows. Verified two
  Alchimie selections update to `Pereche gata`; four Conexiuni selections enable
  `Verifică`; long legacy labels wrap or compact without breaking controls.

One preliminary `test_mobile_contract.py` run used the scraper venv, which lacks Django,
so pytest collected no tests (exit 5). The repo venv full suite then ran and passed those
mobile/hidden-answer contracts as part of all 324 tests.

## Risks / manual review

- `Ușor` is now the initial selection, but players can still choose Normal/Greu and daily
  mode before a session is allocated.
- A local alternate curriculum fixture produced unusually long labels; the UI now handles
  them, but first-action/completion rates should still be playtested with the deployed
  fixture at 320–390 px.
- No scoring, selection, hint, answer, TTL, capacity, or server-authority logic changed.

## Merge recommendation

Green and ready to land as one frontend behavior/docs/release-bundle commit.
