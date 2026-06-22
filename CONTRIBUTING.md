# Contributing — cat_de_roman_esti

## Branch & merge policy

**Direct local merges to `main` are allowed.** Prefer a **feature branch** for substantial
work, then fast-forward / merge it into `main` locally once the gate is green.

- Do substantial work on a **feature branch** (e.g. `feat/…`, `fix/…`); trivial changes may
  land on `main` directly.
- Merge into `main` only when the gate is green (`.github/workflows/ci.yml`: fixture
  validation + ruff + pytest on py3.11/3.12, and the frontend eslint + build).
- **Pushing to `origin` is still opt-in:** assistants must NOT `git push` or open a remote
  PR without an explicit request — local merges to `main` are fine, publishing is not.

_(Relaxed 2026-06-22 from the earlier PR-only rule, by request.)_

## Local quality gate (run before opening a PR)

```bash
python scripts/validate_fixture.py     # KG fixture must be GREEN
pytest -q                              # backend (offline against the bundled fixture)
ruff check                             # lint
( cd frontend && npm run lint && npm run build )   # tsc + eslint + vite build
```

See [`docs/STATUS.md`](docs/STATUS.md) for current phase and [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md)
for the game model. Editing KG content? Use `scripts/expand_content.py` (it regenerates
puzzles via the validator's own BFS and refuses to emit anything the gate would reject).
