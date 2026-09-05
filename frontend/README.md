# cat_de_roman_esti — frontend

Text-only word-game arcade SPA: **React 19.2 + Vite 8.1 + TypeScript** (no graph
visualization — the old force-graph SPA was removed 2026-06-22, see
`../docs/adr/0001-pivot-to-word-game-arcade.md`).

Six word games over the Romanian concept graph, all **server-authoritative**: the
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
npm test             # node --test tests/*.test.mjs (frontend contracts, CI step)
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

Browser journeys follow [ADR-0098](../docs/adr/0098-protect-real-browser-game-journeys.md).
With Python web dependencies available as `python3`, run:

```bash
npm ci
npx playwright install chromium
npm run build
npm run test:e2e
```

The runner starts its own offline anonymous BFF on port 8138. On the fleet host, put
the project `.venv/bin` and the Node 24 runtime first on `PATH`. Failure artifacts live
in ignored `test-results/`; `CDR_E2E_OUTPUT_DIR` can redirect them. The frozen public
seeded starts are in `e2e/seeded-starts.json`; regenerate only after an intentional,
reviewed selection change with `PYTHONPATH=.. python3 e2e/solutions.py --write-starts`.

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
    intrusul.ts       Intrusul: the server owns the answer and score; before the round
                      ends the browser only receives visible tiles and earned feedback.
    perechi.ts        Perechi: pair mappings, provenance and scoring stay server-side;
                      the UI renders solved pairs and the one explicitly earned hint.
    meta.ts           Category taxonomy endpoint (ADR-0011), fetched once per page load.
    auth.ts           Account, private score-copy and verified-ranking transport
                      (same-origin session cookies + X-CSRFToken).
  screens/
    Home.tsx          Arcade lobby: one card per game plus the local records/history panel.
    Alchimie.tsx      Combine two concepts into a new one until you craft the target
                      (à la Infinite Craft).
    CaldRece.tsx      Hidden secret concept; each guess reports hot/cold closeness
                      (à la Contexto — server game key: "contexto").
    Lant.tsx          Type a linked concept and hop word-by-word to the target
                      (à la The Wiki Game).
    Conexiuni.tsx     Group 16 concepts into 4 hidden categories, 4 mistakes allowed
                      (à la NYT Connections).
    Intrusul.tsx      Tap the one concept that does not belong with the other three.
    Perechi.tsx       Eight visible words, four semantic matches; the second tile submits.
    Ranking.tsx       Public online leaderboard, one view per game (opt-in signed-in rows).
  components/
    GameShell.tsx     Shared per-game header: back-to-menu + status-badge slot.
    GameIntro.tsx     Shared "before you play" card: icon, title, how-to, start, daily.
    Hud.tsx           Uniform status cluster: moves/lives/difficulty badges.
    PlayGuide.tsx     Step-by-step how-to-play list used by the intro cards.
    DifficultyPicker.tsx  Shared segmented difficulty control.
    CategoryPicker.tsx    Chip row for a game's category/theme (ADR-0011).
    ResultCard.tsx    Shared end-of-game card: score, "Record!", share/copy, replay.
    Confetti.tsx      One-shot deterministic celebration burst; honours reduced motion.
    AccountBar.tsx    Optional account/ranking controls.
    SoundToggle.tsx   Persisted mute control.
  hooks/              useActiveGame, useSavedGameResume, useAuth, useRecordScore.
  games.ts            Single registry for the six games: routes, titles, accents, icons.
  categories.ts       KG category → color/label map, mirroring the --cat-* CSS variables.
  scores.ts           Offline localStorage personal-best store (per game + per puzzle).
  scoreSync.ts        Upload-only private copy of completed rows for consenting accounts.
  derivedReplay.ts    Bounded replay continuity for the two derived games (opaque ids only).
  share.ts            Deterministic share/copy payload around the server-authored result.
  sound.ts            Web-Audio synthesized SFX (no audio assets).
  *.mjs / *.d.mts     Framework-free logic units (async single-flight, Perechi focus,
                      release recovery) exercised directly by `npm test`.
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
