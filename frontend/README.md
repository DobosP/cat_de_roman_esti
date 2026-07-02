# cat_de_roman_esti — frontend

Text-only word-game arcade SPA: **React 18 + Vite + TypeScript** (no graph
visualization — the old force-graph SPA was removed 2026-06-22, see
`../docs/adr/0001-pivot-to-word-game-arcade.md`).

Four word games over the Romanian concept graph, all **server-authoritative**: the
FastAPI BFF owns the KG, validates every move, and hides answers under
`/api/wordgames/*`; the SPA only renders responses. No API key, no game logic, and
no secrets ever live in the client.

## Develop

```bash
npm install
npm run dev          # Vite dev server on http://localhost:5173
```

`/api/*` is proxied to the BFF at `http://127.0.0.1:8000` (so SPA + API share an
origin). Start the BFF first, e.g. from the repo root:

```bash
make dev             # vite + uvicorn --reload together
# or just the BFF:  uvicorn cat_de_roman_esti.web.app:create_app --factory --port 8000
```

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
  App.tsx             Arcade router — home screen (animated game cards) -> one of the
                      four game screens, with framer-motion AnimatePresence
                      transitions. Owns the toast stack + sound toggle.
  api/
    client.ts         Shared ApiError type for the per-game fetch wrappers.
    alchimie.ts       Typed same-origin wrappers, one module per game, matching the
    contexto.ts       server contract under /api/wordgames/<game>/* (create game,
    lant.ts           get state, guess/combine/move/hint/undo/reset as each game
    conexiuni.ts      defines them).
  screens/
    Alchimie.tsx      Combine two concepts into a new one until you craft the target
                      (à la Infinite Craft).
    CaldRece.tsx      Hidden secret concept; each guess reports hot/cold closeness
                      (à la Contexto — server game key: "contexto").
    Lant.tsx          Type a linked concept and hop word-by-word to the target
                      (à la The Wiki Game).
    Conexiuni.tsx     Group 16 concepts into 4 hidden categories, 4 mistakes allowed
                      (à la NYT Connections).
  components/
    GameShell.tsx     Shared per-game header: back-to-menu + status-badge slot.
    DifficultyPicker.tsx  Shared segmented difficulty control.
    ResultCard.tsx    Shared end-of-game card: score, "Record!", share/copy, replay.
    Toast.tsx         Toast stack; SoundToggle.tsx persisted mute control.
  scores.ts           Offline localStorage personal-best store (per game + per puzzle).
  share.ts            Deterministic share/copy payload around the server-authored result.
  sound.ts            Web-Audio synthesized SFX (no audio assets).
  theme/
    theme.css         Deep dark gradient palette, CSS-variable tokens, glow/shadow,
                      category color map, fonts. (Plain CSS — no Tailwind/postcss.)
    tokens.ts         Category style map (label/color/glow/blurb) shared with TS.
```

## Notes

- Lean dependency set on purpose (install reliability): `react`, `react-dom`,
  `framer-motion` + Vite/TS/ESLint dev tooling. **No Tailwind** — styling is plain
  CSS with CSS variables (no postcss setup).
- The BFF also exposes `GET /api/health` and `GET /api/manifest` (offline-KG trust
  manifest with stable OpenAPI operationIds) — the mobile client contract lives in
  `../docs/MOBILE_CONTRACT.md`.
