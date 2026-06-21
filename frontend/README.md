# cat_de_roman_esti — frontend

Animated semantic-hop game SPA: **React 18 + Vite + TypeScript**.

The player navigates a visible semantic network of Romanian culture, hopping from a
START concept to a TARGET in as few hops as possible. The game is
**server-authoritative**: the FastAPI BFF validates and scores every hop via the
existing Python `HopGame`; the API key never reaches the browser.

## Develop

```bash
npm install
npm run dev          # Vite dev server on http://localhost:5173
```

`/api/*` is proxied to the BFF at `http://127.0.0.1:8000` (so SPA + API share an
origin). Start the BFF first, e.g.:

```bash
PYTHONPATH=/home/dobo/work/cat_de_roman_esti \
  /home/dobo/work/romania_scraper/.venv/bin/uvicorn cat_de_roman_esti.web.app:app --port 8000
```

(The BFF module is built by a separate task; the SPA talks to it only over `/api`.)

## Build

```bash
npm run typecheck    # tsc --noEmit
npm run build        # tsc --noEmit && vite build
```

`vite build` emits the static SPA into `../cat_de_roman_esti/web/static`
(`build.outDir`, `emptyOutDir: true`) — exactly where the FastAPI app mounts
`StaticFiles(html=True)` at `/`. If that build is absent the BFF serves a "run npm
run build" placeholder instead of 500-ing.

## Layout

```
src/
  main.tsx            React root.
  App.tsx             Screen router — useReducer FSM (menu->game->win) with
                      framer-motion AnimatePresence transitions. Owns the active
                      GameState + the toast stack.
  api/
    types.ts          TS types that BYTE-MATCH the server contract
                      (GraphNode/GraphEdge/PuzzleView/GameState + catalog/health).
    client.ts         Typed, same-origin fetch wrappers for every /api endpoint.
  theme/
    theme.css         Deep dark gradient palette, CSS-variable tokens, glow/shadow,
                      category color map, fonts. (Plain CSS — no Tailwind/postcss.)
    tokens.ts         Category style map (label/color/glow/blurb) + canvas palette,
                      shared with the <canvas> graph (CSS vars are invisible to it).
  screens/
    Menu.tsx          Animated category cards from /api/catalog + easy/hard toggle
                      with descriptions + Start. (DONE)
    Game.tsx          TODO STUB (working + playable): drives the server hop loop,
                      keyboard 1–9 hops, reset/exit, shake-on-reject scaffold.
                      NEXT AGENT enriches the presentation/animations.
    Win.tsx           Confetti burst + score count-up + Replay / Next. (DONE)
  components/
    Hud.tsx           start->target chips, hops/par meter, live score, mode+category
                      badges, and the EXPLICIT ordered HOP-TRAIL breadcrumb. (DONE)
    GraphMap.tsx      TODO STUB (working + playable): accessible neighbour-choice
                      list. NEXT AGENT replaces with the react-force-graph-2d
                      force-directed map (glowing nodes, current halo, target ring,
                      visited trail, easy-mode labels + hint glow). Header comment
                      carries the full spec + a skeleton.
```

## TODO handoff

`src/screens/Game.tsx` and `src/components/GraphMap.tsx` are the only intentional
stubs. Both are functional (the game is playable right now via the neighbour list)
and their header comments carry the exact contract + a suggested skeleton. Everything
they import is real, so `tsc --noEmit` and `vite build` pass as-is.

## Notes

- Lean dependency set on purpose (install reliability): `react`, `react-dom`,
  `react-force-graph-2d`, `framer-motion` + Vite/TS/ESLint dev tooling. **No
  Tailwind** — styling is plain CSS with CSS variables (no postcss setup).
- No API key, no game logic, and no secrets in the client — the BFF owns all of it.
