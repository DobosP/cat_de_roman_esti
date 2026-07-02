# ADR-0001: Pivot the web app to a text word-game arcade; remove the graph SPA

Date: 2026-06-22
Status: accepted

## Decision
Pivot the web product to a **text-only arcade of server-authoritative word games**
over the same Romanian concept graph, served under `/api/wordgames/*` by per-game
`APIRouter`s on the shared `wordgames/service.py`. Remove the graph/semantic-hop SPA
and its `/api/games` endpoints entirely: drop `react-force-graph-2d` (bundle
482→289 KB), `GraphMap.tsx`, the graph `Menu/Game/Win/Hud` screens, `web/views.py`,
`web/sessions.py`. **Do NOT build any graph UI unless Paul explicitly reopens it.**
The semantic-hop game survives only as the terminal CLI (`cli.py` + `engine.py`,
untouched).

## Context / why
Landed in `7308ce9` (2026-06-22, "feat: pivot web app to a text word-game arcade (no
graph UI)"); the fourth game (Conexiuni) followed the same day in `5768422`. Stated
motivation: replace the graph-based web game with replayable text formats popular on
Twitch — Alchimie (à la Infinite Craft), Cald sau Rece (à la Contexto/Semantle),
Lanțul Cuvintelor (à la The Wiki Game), later Conexiuni (à la NYT Connections) —
keeping the same KG and the same server-authoritative model (answers hidden
server-side) while cutting the heaviest frontend dependency. Why this ADR exists:
until now the pivot lived only in git history; docs written pre-pivot (frontend
README's GraphMap TODO-handoff, STATUS "What's built") kept describing the removed
graph SPA, and the 2026-07-02 agent-ops triage plan was generated from a stale
snapshot that described the supersession backwards. This is the durable record.

## Consequences
- Frontend deps stay lean (`react`, `react-dom`, `framer-motion`); no canvas/WebGL.
- `/api/games`, the hop-session plumbing, and the graph-map contract are gone; web
  and mobile clients build only on `/api/wordgames/*` (+ `/api/health`,
  `/api/manifest` added 2026-06-29, `125a357`).
- Legacy `kg_puzzles`/`HopGame` stay validated but are unused by the word games.
- Any future graph-visualization idea is a NEW product decision: it requires Paul to
  explicitly reopen it and a superseding ADR — never resurrect it from pre-`7308ce9`
  history, old handoffs, or stale dispatch plans.
