# V87 Contexto action-recovery evidence

Valid until: a bound source, build or tested content input changes — then treat as history.

The actual-BFF baseline probes reproduced two failures: a lost committed win left the
screen playable without its result, and a lost paid clue encouraged a second charge.
The two passing baseline assertions demonstrate those defects; they are not acceptance
tests. Their exact scripts, config, log and observations are retained under `proof/`.

The resulting behavior is documented in [ADR-0126](../../../adr/0126-reconcile-uncertain-contexto-actions.md).
After uncertainty, Contexto reads the authoritative session once without replaying the
action. Failed verification retains input and exposes a persistent read-only retry;
changed ownership offers an explicit load of the currently saved game.

[verification.json](verification.json) binds all application and test sources, the built
manifest, browser content inputs, screenshots and lossless log archives. This is author
verification; the separate [independent code review](../CODE_REVIEW.md) and root release
matrix remain distinct evidence.

- **193/193 native tests** pass, including 16 new controller behavior cases. The initial
  189/192 result and subsequent 192/192 run are retained. Three historical source-shape
  checks were updated to require the stronger ownership and recovery behavior; one
  additional case then covered a foreign saved pointer already present before a POST.
- **Lint, TypeScript and production build** pass. Initial gzip remains **118.90/120 KiB**.
- **20/20 actual-BFF browser cases** pass on the first focused run in **52.9 seconds**:
  ten desktop and ten mobile cases, with no retries or timeout changes. Committed losses,
  uncommitted failures, paid clues, win/give-up adoption, failed GET/manual verification,
  missing sessions and stale or changed ownership are exercised through real API calls.
- The persistent notice and retry are visibly readable beside the retained input on
  [desktop](screenshots/desktop-read-only-recovery.png) and
  [mobile](screenshots/mobile-read-only-recovery.png). Both screenshots were inspected;
  the browser also verifies that the notice is in the viewport. Mutation controls remain
  disabled until verification succeeds.

There were no application or browser-test changes after this focused run. Existing
server fields, score authority, private-answer boundaries and session/request bounds
remain unchanged. These tests do not claim a distributed exactly-once protocol.

Raw logs and proof scripts are preserved with deterministic gzip (`mtime=0`), including
tool-emitted whitespace. `log_sha256` binds the decoded original bytes and
`archive_sha256` binds each committed archive. Original files also remain in task scratch
until the root completes landing cleanup.
