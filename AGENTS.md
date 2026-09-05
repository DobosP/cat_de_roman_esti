# Agent Instructions — cat_de_roman_esti

## Project summary
- Purpose: Romanian word-game arcade — six server-authoritative text games (Alchimie, Intrusul,
  Perechi, Conexiuni, Cald sau Rece, Lanțul Cuvintelor; README.md:9-18) served by a Django BFF
  (`cat_de_roman_esti/web/`) + React SPA (`frontend/`) over the bundled Romanian KG build
  `cat_de_roman_esti/fixtures/kg_sample.json` (data.py:27); the terminal CLI `cat-de-roman` (pyproject.toml:44)
  is the original semantic-hop game. Word-game/session behavior stays bounded, deterministic, test-covered.
- Main runtime: Python ≥ 3.11 (pyproject.toml:9); deploy 3.12, CI 3.12 + 3.14 (ci.yml:34); Node 24
  for the SPA (ci.yml:76). The CLI is stdlib-only; the web app needs the `web` extra pinned via
  `constraints.txt` (pyproject.toml:17-40).
- Status source: `docs/STATUS.md`.

## Fleet context
- Role: RO-EDU consumer: the word-game arcade over the `kg_nodes`/`kg_edges`/`kg_puzzles` products
  (docs/ROEDU_INTEGRATION.md:3-5). Canonical role/status/next: vault note
  `dobo-brain/paul-brain/projects/cat-de-roman-esti.md`
  (fleet view: vault `projects/index.md` + `NOW.md`; agent-ops ADR-0032). Upstream: `romania_scraper` →
  `ro_data_server` · Downstream: none.
- Fleet map + parallel-agent protocol: `~/work/AGENTS.md` (agent-ops ADR-0025/0026). Global session, git,
  scratch and secrets rules: `~/.claude/CLAUDE.md` (agent-ops ADR-0027/0028/0037/0063/0074/0077) — cited here, not restated.
- Delegation: roles and rungs per the `agent-routing` skill (the ladder in `fleet-tiers.sh`); Codex is opt-in (agent-ops ADR-0065).

## Parallel work (mandatory)
- This shared checkout stays on `main`, clean — clean includes untracked (agent-ops ADR-0063): `git status --porcelain`
  is empty when you finish; a stray file blocks the next task-worktree/Ctrl-N session here. A stray file you
  did not write gets reported, not deleted.
- One task = one branch (`<type>/<slug>`) = one worktree `~/work/_worktrees/cat_de_roman_esti/<slug>`, never under `/tmp`:
  `python3 ~/work/agent-ops/scripts/create_task_worktree.py --repo ~/work/cat_de_roman_esti --branch <type>/<slug> --task "..." --write`
  Scratch and one-off scripts: `~/work/_temp/<slug>/`, run against this repo by path (agent-ops ADR-0028).
- Workers never push. The orchestrating session lands green work on `main` (agent-ops ADR-0014) and finishes the landing
  in the same session (agent-ops ADR-0037): delete the verified-merged branch (local + origin), its worktree, `_temp/<slug>/`.
  Unmerged work is deleted only per item, human-confirmed. A branch reaches origin only on land or by
  `ops publish cat_de_roman_esti <branch>` — `ops sync` never creates a remote ref (agent-ops ADR-0077).

## Read first
1. `docs/STATUS.md` — current truth.
2. `README.md` — run modes + doc index.
3. `docs/agent-map.md`, `docs/agent-testing.md`.
4. Content waves only: `docs/CRITIQUE_RUBRIC.md` + the newest `docs/reviews/<wave>/README.md`.
5. Task-specific service/test files; never the whole app, no large build artifacts or pasted source dumps.

## Commands
- Interpreter: `~/work/cat_de_roman_esti/.venv/bin/python` (Python 3.12, Django + pytest-django installed;
  gitignored, lives only in the shared checkout). From a task worktree prefix `PYTHONPATH=.`. Do NOT use the
  `romania_scraper` venv: it has no Django — `pytest --co` = 7 collection errors, 402/898 tests (verified 2026-09-05).
- Install into a fresh venv: `pip install -c constraints.txt -e ".[dev,web]"` (ci.yml:48)
- Targeted test: `PYTHONPATH=. ~/work/cat_de_roman_esti/.venv/bin/python -m pytest tests/test_wordgames_session_store.py -q` → 16 passed
- Full suite: same interpreter, `-m pytest -q` (current result in `docs/STATUS.md`; load-sensitive); accounts suite:
  `CAT_ACCOUNTS_ENABLED=1 CAT_DEBUG=1 <interpreter> -m pytest -q tests/accounts` (ci.yml:61)
- Content gates: `<interpreter> scripts/validate_fixture.py` → `GREEN: fixture is valid (0 errors)` ·
  `<interpreter> scripts/validate_games_pack.py` → `games pack GREEN` (ci.yml:51-55)
- Lint: `<interpreter> -m ruff check` · Whitespace: `git diff --check`
- Frontend, only when `frontend/` changes: `cd frontend && npm ci && npm test && npm run lint && npm run build`
  (ci.yml:84-95); commit the regenerated `cat_de_roman_esti/web/static` + `.vite/manifest.json` with it (ADR-0020).
- Run the app on this host: `CDR_PYTHON=~/work/cat_de_roman_esti/.venv/bin/python ./run.sh` (run.sh:26 defaults to
  the romania_scraper venv).

## Safety
- Never read or print secret values; names only: `ROEDU_API_URL`, `ROEDU_API_KEY` (`.env.example`); values deploy per agent-ops ADR-0027.
- Landing policy for this repo: ADR-0004 — direct local merge to `main` once the CI gate is green; pushing to
  origin is explicit-request-only. Never land a red suite.
- Keep game/session fixes narrow and test-backed; session stores stay bounded. Worker briefs name the expected
  TTL/size/session behavior and the targeted test command.
- Content changes pass both validators and the critique rubric (`docs/CRITIQUE_RUBRIC.md`, ADR-0067); never
  hand-edit `web/static` or fixture JSON.
- The accounts stack (`CAT_ACCOUNTS_ENABLED=1`) collects data from possibly-minor users: production stays
  anonymous until the go-live checklist in `docs/DEPLOY.md` is satisfied (DEPLOY.md:35-40).

## Docs discipline (mandatory)
- `docs/STATUS.md` is this repo's single source of current truth. On conflict: `docs/STATUS.md` > newest-dated ADR in
  `docs/adr/` > everything else. An undated doc is history, not instructions.
- Definition of done for any change of behavior, architecture, status, or decision — same commit: update
  `docs/STATUS.md` (facts + `Last verified: YYYY-MM-DD`); a decision made or reverted gets `docs/adr/NNNN-<slug>.md`
  (claim the number in `docs/adr/README.md`; flip the superseded ADR's `Status:`).
- ADRs are append-only. No decision language ("we use X", "default is") in READMEs/guides — link the ADR.
- Continuation lives in the tab handoff and the vault task note (agent-ops ADR-0078), never a new dated handoff. Dated
  records open with `Valid until: <event> — then treat as history.`
- Budgets: this file ≤ 80 lines, `CLAUDE.md` ≤ 12 non-blank, `docs/STATUS.md` ≤ 120, `docs/agent-map.md` ≤ 60,
  `docs/agent-testing.md` ≤ 80. History overflows to `WORKLOG.md`. Convention: `agent-ops/docs/29-doc-governance.md`.
