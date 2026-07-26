# V39 local daily circuit result

Commit: `451ec32` (`feat(web): add local daily circuit`)

Base: `670810b` (`feat(accounts): verify bounded public rankings`)

Implemented:

- a compact mobile-first `Circuitul de azi` Home card derived only from the
  normalized local score-history snapshot;
- exact six-game order: Alchimie, Intrusul, Perechi, Conexiuni, Cald sau Rece,
  Lanțul Cuvintelor;
- best retained score for the exact valid daily identity, with zero/negative
  completed runs counted and every contribution clamped to 0–1000;
- six-game total clamped to 0–6000;
- local/device-only explanation, labelled status/list semantics, and no circuit
  action, API, upload, telemetry, or automatic game start;
- `Azi ✓` on each completed game card;
- defensive handling for malformed/unknown/imported histories and impossible
  calendar dates.

Verification:

- focused helper/UI/accessibility cases: 6/6 passed;
- full frontend test files: 20/20 passed;
- frontend lint: passed;
- frontend typecheck: passed;
- canonical Vite build: 470 modules;
- initial JS/CSS gzip: 119.02/120 KiB;
- static cache/web tests: 16/16 passed;
- session-store regression: 16/16 passed;
- `git diff --check`: passed.

No documentation, server API/model, session behavior, TTL, storage cap, daily
identity, answers, catalogs, upload, telemetry, or public aggregate was changed.
