# V89 independent Conexiuni recovery review

Valid until: any bound implementation, native-test or dependency file changes — then re-review.

Date: 2026-09-08. Baseline: `b614bfe735a27b9703025420daf603118f6a7f74`.
Decision: **accept the reviewed code; no code blockers**. The final focused browser
receipt and full V89 integration matrix remain landing requirements. This reviewer
did not repeat heavy suites or author the implementation.

Exact implementation/native-test/ADR hashes and 14 byte-identical dependencies are in
[conexiuni-review.json](conexiuni-review.json). The canonical source-set SHA-256 is
`3e61204c0df8e6f1734c9514b2729aa2f7691c01312884fbb1b2e5fb3f2311d9`.

## Accepted behavior

Guess, clue and manual verification share one synchronous action owner. Acquisition
happens before React state updates. A stale completion cannot release a newer ticket.
Each still-owned failed mutation performs one same-session GET; the helper has no
POST callback, automatic replay or retry loop. Failed reads keep a persistent recovery
action and lock submission, tile changes, keyboard shortcuts, clues, shuffle and clear.

Recovered state replaces the complete server response. Earned groups, redacted clues,
mistake counts and terminal results remain authoritative. Selection keeps only ids that
are still unsolved. Existing score receipts record a recovered terminal result once and
conditionally clean up its saved pointer. No lost response creates a local score or clue.

GET contains no transient `one_away` result. Recovery therefore uses neutral feedback;
only the original successful guess response can claim three-of-four. A confirmed 409
duplicate retains its four ids through failed verification. Once a read succeeds, the
same still-visible combination stays blocked without a three-of-four claim. Ordinary
successful one-away guidance and order-independent selection matching remain intact.

Ownership is checked before mutation and after asynchronous replies. Unmount, a new-round
attempt and saved-game adoption invalidate tickets. Another saved id pauses the old game
and enters explicit current-game resume. An owned 404 conditionally forgets only its id.
An uncertain exit preserves the pointer; ordinary live exits conditionally remove their
own pointer. Stable-null storage permits local play under the unchanged shared helper.

The backend, API client, shared owner, resume and score dependencies are byte-identical
to baseline. Sliding TTL remains 7,200 seconds, maximum sessions 1,000 per game, requests
64 KiB, mistakes four and clues two. Session transactions, bounded history and private
unsolved group membership remain unchanged.

## Evidence and limits

The four actual baseline browser/BFF cases committed a clue, solved group, final win or
final loss, then replaced only the reply with 503. None issued a client GET. The clue was
absent, a solved group left 16 selectable tiles, and terminal results were unrecorded.
Retrying the first lost clue consumed clue two: the captured final score was 50 instead
of 150. I inspected the reproduction script and captured state fields.

The native receipt has 193 passes and zero failures. Its initial seven failures were
stale source-shape assertions; the adjusted tests still assert ownership, duplicate
blocking, honest feedback and conditional exit behavior. Lint/build passed, with the
initial bundle at 118.92/120 KiB. The first focused browser run had 18 passes and eight
exact-text locator failures across four desktop/mobile journeys; error snapshots show
the requested status text alongside the existing decorative glyph. Those initial bytes
remain evidence, and the corrected test selectors require a completed run.

Visual inspection found the initial desktop recovered-win result rendered, though its
controls were below the internal scroll position. The initial desktop read-only recovery
image was blank background while a mocked-clock outer transition was unsettled. The
builder was asked for settled screenshots. These observations concern evidence capture;
they do not establish a product defect or substitute for final visual verification.

GET confirms current state without attributing changes to one browser or request. Saved
pointer ownership is a local guard, not a distributed exactly-once protocol. A lost
one-away reply may receive one explicit 409 on retry before the duplicate is blocked.
This review does not establish human enjoyment or replace Romanian-player and real-device
release checks.

## Final lane evidence supplement

The later [durable lane verification](conex-action/verification.json) completes the
focused checks left pending above: **26/26 behavior cases** pass, followed by **2/2
stricter screenshot cases**. I verified all nine lane source hashes, 24 lossless archive
hashes plus decoded hashes/byte counts, and 28 image hashes against actual files. The
final browser spec differs from the passing behavior spec only by advancing 500 ms of
mocked animation frames and asserting outer-screen opacity. No product source changed.

I independently viewed the [final desktop recovery image](conex-action/final-read-only-recovery-desktop.png):
the recovery copy and button are visible, and the board controls are visibly disabled.
The [final desktop win image](conex-action/behavior-recovered-win-desktop.png) shows the
server score 1000 and all result actions. Initial blank/clipped captures remain preserved.
The full V89 integration matrix and release checks are still separate requirements.
