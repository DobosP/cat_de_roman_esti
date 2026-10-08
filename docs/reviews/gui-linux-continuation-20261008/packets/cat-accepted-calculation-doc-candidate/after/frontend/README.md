# cat_de_roman_esti — frontend

Text-only word-game arcade SPA: **React 19.2.7 + Vite 8.3.3 + TypeScript 7.0.2** (no graph
visualization — the old force-graph SPA was removed 2026-06-22, see
`../docs/adr/0001-pivot-to-word-game-arcade.md`).

Six word games over the Romanian concept graph, all **server-authoritative**: the
Go backend owns the sealed reviewed content, validates every move, and hides answers under
`/api/wordgames/*`; the SPA only renders responses. No API key, no game logic, and
no secrets ever live in the client.

## Develop

```bash
npm ci
npm run dev          # Vite dev server on http://localhost:5173
```

`/api/*` is proxied to Go at `http://127.0.0.1:8000` (so SPA + API share an
origin). Start the native server first, or use the combined launcher from the repo root:

```bash
make dev             # Go API + Vite frontend development
# API only: ./run.sh
# Restart after Go changes; Vite reloads frontend changes.
```

## Build

```bash
npm test             # node --test tests/*.test.mjs (frontend contracts, CI step)
npm run lint         # owning GUI gate: Oxlint/tsgolint + native/SDK AST contracts
npm run typecheck    # verified native TypeScript 7 --noEmit
npm run build        # native typecheck + Vite build + startup-transfer/font gates
```

The selected Node 26.10.0/npm 12.2.0 toolchain and managed-output prerequisites are
recorded in [ADR-0184](../docs/adr/0184-native-spa-toolchain-and-managed-output.md).
`vite build` emits `frontend/dist`; the owning asset sync copies the managed
output to `go-backend/embedfs/dist` before rebuilding the Go server. The original
tracked 30-file `web/static` bundle and legacy archive stay frozen. An absent
managed index returns HTTP 503; build alone does not update an existing server binary.
The lint entry point requires the owning Linux wrapper's current context, selected
configuration and installed kit. Complete normalized validation remains pending.

[ADR-0185](../docs/adr/0185-accepted-eager-startup-bundle-accounting.md) records Paul's accepted
startup calculation: all entry/static JS/CSS plus the immediately mounted
`src/components/AccountBar.tsx` root and its recursive static dependencies,
counted once across shared files/cycles. Missing mandatory roots/imports or emitted
assets refuse the check. Other dynamic game routes and further lazy children remain
excluded. `checkInitialBundle` always requires AccountBar after integration;
default `collectInitialBundleFiles(manifest)` callers and frozen historical
closures retain their static-only scope.

The separate two-path calculator amendment is source-accepted, **UNAPPLIED and
UNQUALIFIED**. Its four retained and seven new tests (11 total) are **NOT RUN**
under the amended source; current manifest/startup gzip measurements are unacquired.
The frontend default remains 120 KiB (122,880 bytes), summing each selected JS/CSS
file's gzip level-9 size; existing limit configuration and Latin/Latin Extended
Fredoka/Inter subset checks remain. Fonts are checked separately from JS/CSS bytes.
The canonical 40,960-byte JS ceiling/30,720-byte target and separate CSS policy
remain independent requirements; no new total, savings or compliance is claimed.

## Layout

Browser journeys follow [ADR-0098](../docs/adr/0098-protect-real-browser-game-journeys.md).
The current runner starts an already-built Go server (`CDR_NATIVE_BINARY`, default
`build/cat-server`) and uses the native private `cat-browser-plan` helper.
Complete the owning managed-assets/server/planner prerequisites before these Linux
browser steps; Python helpers below are optional offline references:

```bash
npm ci
npx playwright install chromium
npm run build
npm run test:e2e
```

The runner starts its own native anonymous Go server on port 8138 (`CDR_E2E_PORT` overrides it).
Use the selected Node 26 toolchain and the owning built server/planner inputs. Failure artifacts live
in ignored `test-results/`; `CDR_E2E_OUTPUT_DIR` can redirect them. The frozen public
seeded starts are in `e2e/seeded-starts.json`; regenerate only after an intentional,
reviewed selection change with `PYTHONPATH=.. python3 e2e/solutions.py --write-starts`.
Rendered accessibility and keyboard coverage follow [ADR-0103](../docs/adr/0103-make-game-status-keyboard-reachable.md).

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
- Selected tooling and managed-output handling follow [ADR-0184](../docs/adr/0184-native-spa-toolchain-and-managed-output.md).
  Native TypeScript 7 owns diagnostics; the separately bound TypeScript 6 package is
  for required AST/transpilation APIs. Current normalized gate qualification is pending.
- Preserve the frozen original30 files/archive; managed output sync and reviewed source
  retirement follow ADR-0184. Historical reports keep their captured closure scopes;
  [ADR-0185](../docs/adr/0185-accepted-eager-startup-bundle-accounting.md) does not recompute them.
- The Go backend also exposes `GET /api/health` and `GET /api/manifest` (offline-KG trust
  manifest with stable OpenAPI operationIds) — the mobile client contract lives in
  `../docs/MOBILE_CONTRACT.md`.
