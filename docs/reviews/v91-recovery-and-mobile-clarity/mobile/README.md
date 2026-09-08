Valid until: a later shared-layout change or content revision supersedes these bound V91 observations — then treat as history.

# V91 shared mobile status and notices

The final shared layout keeps the title, Exit and every HUD badge visible, with
notifications in a separate row above the scrollable game viewport. The production
bundle passes **14 focused browser cases, zero failures/retries**, plus **10 focused
native tests**. Typecheck and lint pass. The coordinating root produced the combined
build at **119.04/120 KiB**; this lane never generated static assets.

## Before and after

Baseline is clean local main `e2e03638b90fc9248c33f70eedaa8c9c5fbd87ad` and its V90
static bundle, served on 8189. Candidate screenshots and final checks use the combined
production bundle on the task-worktree BFF, also on 8189 after restarting the server.
[source-bindings.json](source-bindings.json) binds baseline source/static and the exact
installed Toast API. [built-source-bindings.json](built-source-bindings.json) binds all
candidate frontend source, static assets and the focused browser test. Its
[post-run recheck](built-source-recheck.json) has zero mismatches.

At 320px, the original header hid the title and offered only 220px to most HUDs:

| Game | Original HUD content/available px | Final content/available px |
| --- | ---: | ---: |
| Alchimie | 458 / 220 | 292 / 292 |
| Intrusul | 169 / 168.5 (rounding; its one badge fit) | 292 / 292 |
| Perechi | 282 / 220 | 292 / 292 |
| Conexiuni | 299 / 220 | 292 / 292 |
| Cald sau Rece | 262 / 220 | 292 / 292 |
| Lanț | 278 / 220 | 292 / 292 |

The same five HUDs clipped later badges at 390px. Desktop HUDs already fit. The four
toast-based resume paths placed their old notice at y16–56 across the header at y14–66
(Cald sau Rece has a small additional top offset). In the final 320px Alchimie capture,
the notice is y8–52 and the complete header begins at y70. Intrusul and Perechi retain
their existing inline resume copy.

The primary raw pairs are `before-touch/*-{320,390}-{live,resume}.png`,
`before/*-1280-{live,resume}.png` and `after-built/*-{320,390,1280}-{live,resume}.png`.
The corresponding `metrics-*.json` preserve exact bounds. Representative links:
[Alchimie before](before-touch/alchimie-320-resume.png),
[Alchimie after](after-built/alchimie-320-resume.png),
[Perechi before](before-touch/perechi-320-resume.png),
[Perechi after](after-built/perechi-320-resume.png),
[desktop notice](after-built-verified-notices/contexto-1280-resume.png).

The builder visually inspected all six 320px baseline resume screenshots and every
final resume screenshot at 320/390/1280, plus the long-text/short-screen stress and
original failure images. Captures await fonts and finite animations; final stress
screenshots are in `focused-built-attachments/`. Other raw live captures support the
recorded geometry; they do not claim separate human/device acceptance.

## Focused verification

[The complete Playwright report](focused-built-report.json.gz) contains all 14 results,
geometry attachments and exact PNG attachment bodies. It records 14 expected, zero
unexpected, zero flaky and zero skipped cases in 141.279 seconds. The
[terminal log](focused-built.log.gz) is retained separately. The test runs each game
at desktop 1280px and mobile 320/390px: intro, live board, resume, scrolled header,
finished result, real clipboard-failure feedback and keyboard notice dismissal. All
six remain playable through their seeded solutions. Checks verify screen width,
visible full titles, every badge inside the header, secondary sticky controls below
it, and notices outside the game viewport.

Two additional cases use a presentation-only long Romanian label and 200% root text
size, then a 320×480 viewport with the inventory search focused. They preserve gameplay
state. The initial Alchimie h2 overflow is reproduced on baseline as 350px inside320px;
the shared heading wrap brings it to320px. Focus stays reachable after the short-screen
sticky fallback. Actual keyboard opening, physical safe areas and human-player
acceptance remain unrun; preserved CSS safe-area rules and browser emulation are not
claims about real devices.

Commands use the shared Python venv on PATH and Node24.20.0/npm11.19.0. Exact scratch
configs/runners are archived as `.mjs.gz` files. The focused command is the equivalent
of `playwright test mobile-status-notices.spec.mjs --reporter=list,json` against the
already running candidate BFF. `native-focused-final.log.gz`, `typecheck-final.log.gz`
and `lint.log.gz` preserve the relevant narrow checks. Full integration belongs to
the root V91 receipt.

## Preserved failures and limits

- The first baseline runner waited for a toast in Intrusul, whose resume feedback was
  already inline, and timed out. `capture-initial-failed.mjs.gz` and
  `before-320-initial-failed.log.gz` retain that harness error. The corrected runner
  waits for the actual resume text in each game.
- The first focused dev run passed12 lifecycle cases and failed2 text-size cases on
  the real 350px heading overflow. Its log, exact failure screenshots/contexts and
  traces remain under `focused-dev-results/`. The two corrected stress cases passed,
  followed by the full14-case built-static pass. An incorrect searchbox locator in
  the initial test was corrected before that assertion was reached; it is not a
  separately observed product failure.
- An inspection initially suggested missing desktop Cald sau Rece/Lanț notices.
  Original-detail viewing, raw pixels, unchanged before/after DOM bounds and repeated
  captures confirmed the notices were present. The expiry/autofocus hypothesis was
  withdrawn; `inspect-notice.*` and `after-built-verified-notices/` preserve the probe.
- Vite dev-start optional-esbuild warnings and Django's streaming-response warning are
  retained in logs. Neither prevented the production build or focused checks.
- At 320px the existing Conexiuni coach text is cramped. Its baseline screenshot shows
  the same wrapping; this lane changes the shared header/notice layout, not that coach.

[ADR-0139](../../../adr/0139-visible-mobile-status-and-notices.md) records the decision.
The package's ToastStack remains unchanged, including live announcements, visual
tokens, dismiss buttons and the3.6-second lifetime. No game/backend/fixture/upstream
changes were made by this lane. Original JSON reports keep all screenshot attachment
bodies; redundant extracted resume copies and exploratory duplicate captures remain
in scratch until the authorized landing cleanup.

[manifest.json](manifest.json) hashes every retained raw artifact and its uncompressed
bytes. Gzip payloads use mtime0. `archive.py.gz` records the deterministic packaging
and verifies exact scratch copies before removing a generated duplicate from this
review folder.
