Valid until: a superseding accepted calculation decision — then treat as history.

# ADR-0185: Count immediately mounted AccountBar in startup JS/CSS

Date: 2026-10-08
Status: accepted by Paul; source amendment unapplied and unqualified; actual Linux validation pending
Supersedes: ADR-0020 first-load JS/CSS accounting only; ADR-0184 tooling/output and other ADR-0020 limits remain.

## Decision

For the frontend build's initial-transfer check, count the union of every Vite
entry's recursive static JS/CSS closure and the immediately mounted
`src/components/AccountBar.tsx` root's recursive static JS/CSS closure. Count
shared emitted files once and terminate cycles through a shared visited set.
Require the fixed AccountBar root in `checkInitialBundle`; caller/environment
options cannot remove that root. Missing or malformed required eager root/import
bindings and missing emitted JS/CSS files refuse the check. Other dynamic game
routes and further dynamic descendants remain outside this bounded startup set.

Sum each selected file's gzip level-9 bytes. Keep the frontend default at
120 KiB (122,880 bytes), its existing limit configuration and its separate exact
Fredoka/Inter Latin and Latin Extended font-subset checks. Fonts, images and other
non-JS/CSS assets are not added to this sum. The canonical `cat-initial`
JavaScript ceiling of 40,960 bytes and target of 30,720 bytes, and the separate
CSS policy, remain independent unchanged requirements.

Keep `collectInitialBundleFiles(manifest)` static-only by default; explicit
bounded `eagerRoots` support the build check without changing other callers.
Frozen historical per-key baselines, `gui-assets initial_gzip_bytes` and
original observations retain their exact captured static-only scopes.

## Context / why

Paul directly accepted this calculation on 2026-10-08: "accept this new
calculation update all documentation with this new calculation and continue".
`App.tsx` defines AccountBar with React lazy import syntax, then mounts it
unconditionally in the initial Suspense shell before any play action. Auth state
can make its rendered UI empty only after its module has been fetched. Dynamic
syntax therefore does not exclude this immediately requested chunk from startup
accounting. Game chunks remain route-lazy and outside this bounded startup set.

The retained original Vite manifest at
`93066854f67245d4b70c0ea97dc2401445a3218c` binds that source-relative root.
It is historical source evidence, not a fresh manifest or observed startup sum.
The existing entry/static-only calculator omits AccountBar; the accepted separate
two-path amendment changes that calculator and its meaningful source contracts.
It does not change application/auth/score/game/motion behavior or add product bytes.

## Consequences

At this decision checkpoint, the calculator amendment is **SOURCE ACCEPTED,
UNAPPLIED and UNQUALIFIED**. Four original contracts remain, seven are added
(11 total); the amended suite is **NOT RUN**. Actual current manifest, emitted
file inventory, gzip total and appropriate Linux checks remain pending. This
decision records no new measurement, savings, budget PASS, image or release identity.

The stricter calculation can expose a genuine failure of the unchanged 120 KiB
default. Preserve that failure and its exact inputs; do not omit AccountBar,
weaken assertions or rewrite original numbers to obtain a pass. Preserve
ADR-0020's historical115.34KiB body/evidence and all original baseline reports.

[ADR-0184](0184-native-spa-toolchain-and-managed-output.md) still governs selected
tooling and managed output; React19 and UI0.3 remain throughM1. PROGRAM E3's real
budget-red/formal M0/M1 constraints, actual same-final-SHA trust -> GREEN unit ->
canonical KIT_BUMP, device/M2, S0b/teacher/social/live/soak and production holds
remain. Immutable core1.2 release/tag identities are unchanged. Current facts
and future owner obligations live in [STATUS](../STATUS.md) and the
[S1 plan](../execplans/s1-cat.md); source acceptance grants no Windows execution
authority or runtime qualification.
