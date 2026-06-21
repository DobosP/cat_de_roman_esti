# Contributing — cat_de_roman_esti

## Branch & merge policy

**No direct commits, merges, or pushes to `main`.** `main` is integration-only and moves
**exclusively through reviewed pull requests**.

- Do all work on a **feature branch** (e.g. `feat/…`, `fix/…`).
- Open a **pull request** into `main`; never `git merge`/`git push` straight to `main`,
  and never fast-forward `main` locally to sidestep the PR.
- A PR may merge only when **CI is green** (`.github/workflows/ci.yml`: fixture validation
  + ruff + pytest on py3.11/3.12, and the frontend eslint + build) and it has been reviewed.
- This applies to automated assistants too: commit to the feature branch, then **stop and
  hand off** — do not push or merge to `main` without an explicit request.

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
