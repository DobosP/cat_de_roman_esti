# cat_de_roman_esti — frontend

Text-only word-game arcade SPA: **React 19.2 + Vite 8.1 + TypeScript** (no graph
visualization — the old force-graph SPA was removed 2026-06-22, see
`../docs/adr/0001-pivot-to-word-game-arcade.md`).

Four word games over the Romanian concept graph, all **server-authoritative**: the
Django BFF owns the KG, validates every move, and hides answers under
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
# or just the BFF:  python -m cat_de_roman_esti.web --port 8000
```

## Build

```bash
npm run lint         # ESLint 10 flat-config checks
npm run typecheck    # tsc --noEmit
npm run build        # typecheck + Vite build + initial-transfer/font gates
```

`vite build` emits the static SPA into `../cat_de_roman_esti/web/static`
(`build.outDir`, `emptyOutDir: true`) — exactly where Django/WhiteNoise serves it.
The post-build check follows recursive static imports in Vite's manifest, enforces
the 120 KiB initial JS/CSS gzip ceiling, and verifies that only Latin + Latin
Extended Fredoka/Inter fonts shipped (ADR-0020). If the build is absent the BFF
serves a "run npm run build" placeholder instead of 500-ing.

## Layout

```
src/
  main.tsx            React root.
  App.tsx             Arcade router — eager home shell + lazy game/ranking routes,
                      LazyMotion/AnimatePresence transitions, and the toast stack.
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
    AccountBar.tsx    Optional account/ranking controls.
    SoundToggle.tsx   Persisted mute control.
  scores.ts           Offline localStorage personal-best store (per game + per puzzle).
  share.ts            Deterministic share/copy payload around the server-authored result.
  sound.ts            Web-Audio synthesized SFX (no audio assets).
  styles/
    arcade.css        Deep dark palette, CSS-variable tokens, layout, and game styles.
    fonts.css         Explicit Romanian-capable Latin/Latin Extended font faces.
  theme.ts            @roedu/ui theme override.
```

## Notes

- Styling is plain CSS with CSS variables; there is no Tailwind/PostCSS layer.
- Tooling is pinned by the lockfile to ESLint 10.7 flat config, typescript-eslint
  8.63, and TypeScript 5.9; TypeScript 7 is not yet in typescript-eslint's peer range.
- Per ADR-0020, frontend source changes include the matching tracked `web/static`
  bundle and `.vite/manifest.json`; backend-only changes leave that bundle alone.
- The BFF also exposes `GET /api/health` and `GET /api/manifest` (offline-KG trust
  manifest with stable OpenAPI operationIds) — the mobile client contract lives in
  `../docs/MOBILE_CONTRACT.md`.
