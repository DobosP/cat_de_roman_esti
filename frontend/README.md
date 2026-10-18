# cat_de_roman_esti — frontend

Text-only arcade GUI source: **Preact 11.0.0 + preact-iso 2.12.2 + Vite 8.3.3 + TypeScript 7.0.2** on all eight app paths, including both Alchimie modes ([ADR-0202](../docs/adr/0202-m3-remaining-preact-screens.md), [ADR-0204](../docs/adr/0204-native-preact-state-for-challenge.md)). The frozen React bundle remains for explicit rollback; accepted milestones and exact-source qualification are recorded in [STATUS](../docs/STATUS.md). There is no graph visualization; the old force-graph SPA was removed 2026-06-22 ([ADR-0001](../docs/adr/0001-pivot-to-word-game-arcade.md)).

Six word games over the Romanian concept graph, all **server-authoritative**: the
Go backend owns the sealed reviewed content, validates every move, and hides answers under
`/api/wordgames/*`; the SPA only renders responses. No API key, no game logic, and
no secrets ever live in the client.

## Develop

From the repository root, use the actual trusted task worktree and the matching
qualified `GATE_SHA`/`GATE_TREE_SHA256` pair required by the [root launcher guide](../README.md#one-command-local):

```bash
./run.sh dev         # pinned-container Go API + Vite HMR on http://localhost:5173
# make dev is the same launcher; ./run.sh serves the managed production build.
```

`/api/*` is proxied to the same-container Go API at `127.0.0.1:8000`.
`PORT` changes only the loopback host API publication; Vite stays on 5173.
Source/index edits hot-reload; restart after backend/configuration/dependency changes.
GUI installs/builds/checks use the owning pinned wrapper, not host npm/Node/Go.
HMR edits do not create a new qualified source identity.

## Build

These are inner commands for the owning pinned shell, from `/work/frontend`;
use the exact-SHA unit/full entry points and cadence in [agent-testing](../docs/agent-testing.md).

```bash
npm test             # original Node contracts plus pinned plain-Preact browser tests
npm run lint         # owning GUI gate: Oxlint/tsgolint + native/SDK AST contracts
npm run typecheck    # native TypeScript 7 --noEmit
npm run build        # native typecheck + Vite build + startup-transfer/font gates
```

The selected Node 26.10.0/npm 12.2.0 toolchain and managed-output prerequisites are
recorded in [ADR-0184](../docs/adr/0184-native-spa-toolchain-and-managed-output.md).
`vite build` emits `frontend/dist`; the owning asset sync copies the managed
output to `go-backend/embedfs/dist` before rebuilding the Go server. The original
tracked 30-file `web/static` bundle and legacy archive stay frozen. An absent
managed index returns HTTP 503; build alone does not update an existing server binary.
The lint entry point requires the owning Linux wrapper's current context, selected
configuration and installed kit. Current qualification belongs to [STATUS](../docs/STATUS.md); a source change or standalone build is not a milestone pass.

[ADR-0185](../docs/adr/0185-accepted-eager-startup-bundle-accounting.md) records the accepted
startup policy for the earlier React checkpoint, including mounted AccountBar.
The current `checkInitialBundle` additionally requires `src/screens/Home.tsx`:
it charges entry/static JS/CSS, `src/components/AccountBar.tsx`, Home and both
roots' recursive static dependencies once across shared files/cycles. Missing
required roots/imports or emitted assets refuse the check. Further dynamic game
edges stay outside this startup helper; default `collectInitialBundleFiles` callers
and frozen historical closures retain their static-only/captured scope.
The separate current route evaluator charges each selected screen/mode leaf, entry,
mandatory AccountBar and every recursive static dependency ([ADR-0202](../docs/adr/0202-m3-remaining-preact-screens.md)); required lazy leaves are never omitted.

Historical React checkpoint only: startup was 122,743/122,880 bytes; FULL2db
passed frontend319/319 but failed six of900 browser cases at the untrusted HTTP
gate origin. Its early browser-capability source/focused checks were recorded
**NOT RUN** (CORE_REQUESTS REQ-6). Preserve those receipts as source-scoped history;
they describe neither current results nor a remaining device gate. [ADR-0199](../docs/adr/0199-owner-no-device-checkpoint-agent-lands-m3-m4.md) removes device testing.
The frontend default remains 120 KiB (122,880 bytes), summing each selected JS/CSS
file's gzip level-9 size; existing limit configuration and Latin/Latin Extended
Fredoka/Inter subset checks remain. Fonts are checked separately from JS/CSS bytes.
The canonical 40,960-byte JS ceiling/30,720-byte target and separate CSS policy
remain independent requirements. Current measured results and acceptance are in [STATUS](../docs/STATUS.md); this guide asserts no new compliance or performance result.

## Layout

Browser journeys follow [ADR-0098](../docs/adr/0098-protect-real-browser-game-journeys.md).
The current runner starts an already-built Go server (`CDR_NATIVE_BINARY`, default
`build/cat-server`) and uses the native private `cat-browser-plan` helper.
Complete the owning managed-assets/server/planner prerequisites before these Linux
browser steps, inside the pinned runner from `/work/frontend`. These inner commands
do not replace the canonical full supervisor or sync/rebuild the Go binary by themselves:

```bash
npm ci
npx playwright install chromium
npm run build
npm run test:e2e
```

The runner starts its own native anonymous Go server on port 8138 (`CDR_E2E_PORT` overrides it).
Use the selected Node 26 toolchain and the owning built server/planner inputs. Failure artifacts live
in ignored `test-results/`; `CDR_E2E_OUTPUT_DIR` can redirect them. The frozen public
seeded starts in `e2e/seeded-starts.json` remain frozen during GUI migration.
`PYTHONPATH=.. python3 e2e/solutions.py --write-starts` is the retained reference
regeneration command, not a GUI migration step. New GUI case inventory entries use
the committed discovery generator (ADR-0202), preserving every original case/assertion.
Rendered accessibility and keyboard coverage follow [ADR-0103](../docs/adr/0103-make-game-status-keyboard-reachable.md).

```
src/
  main.tsx            Preact root (.roedu-root wrapper + preact-iso LocationProvider).
  App.tsx             Literal route switch + lazy selected screen (including Home),
                      mandatory AccountBar, kit Presence frames, and the toast stack.
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
    Alchimie.tsx      URL/saved-round mode selector for independent lazy leaves.
    AlchimieChallenge.tsx  Scored target-crafting rounds.
    AlchimieExplore.tsx    Saved collection, recipes, goals and discovery journal.
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
  categories.ts       Literal KG category → color/label metadata.
  scores.ts           Complete public score-store compatibility facade (ADR-0203).
  scores/             Shared core/read/record plus Home daily/history modules.
  scoreSync.ts        Upload-only private copy of completed rows for consenting accounts.
  derivedReplay.ts    Bounded replay continuity for the two derived games (opaque ids only).
  share.ts            Deterministic share/copy payload around the server-authored result.
  sound.ts            Web-Audio synthesized SFX (no audio assets).
  *.mjs / *.d.mts     Framework-free logic units (async single-flight, Perechi focus,
                      release recovery) exercised directly by `npm test`.
  styles/
    arcade.css        Deep dark palette, CSS-variable tokens, layout, and game styles.
    fonts.css         Explicit Romanian-capable Latin/Latin Extended font faces.
    theme.css         @roedu/ui token overrides under .roedu-root.
```

## Notes

- Styling is plain CSS with CSS variables; there is no Tailwind/PostCSS layer.
- Selected tooling and managed-output handling follow [ADR-0184](../docs/adr/0184-native-spa-toolchain-and-managed-output.md).
  Native TypeScript 7 owns diagnostics; the separately bound TypeScript 6 package is
  for required AST/transpilation APIs. Current exact-source qualification is in STATUS.
- Preserve the frozen original30 files/archive; managed output sync and reviewed source
  retirement follow ADR-0184. Historical reports keep their captured closure scopes;
  [ADR-0185](../docs/adr/0185-accepted-eager-startup-bundle-accounting.md) does not recompute them.
- The Go backend also exposes `GET /api/health` and `GET /api/manifest` (offline-KG trust
  manifest with stable OpenAPI operationIds) — the mobile client contract lives in
  `../docs/MOBILE_CONTRACT.md`.
