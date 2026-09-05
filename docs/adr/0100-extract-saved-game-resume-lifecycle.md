# ADR-0100: Extract the saved-game resume lifecycle

Date: 2026-09-06
Status: accepted

## Decision

Route all six React game screens through one typed saved-game resume hook. Its narrow
framework-free core reads one opaque active ID, performs one GET, classifies terminal,
missing, and transient outcomes, applies the selected ID-retention policy, and exposes a
subscription that suppresses delivery after unmount. React Strict Mode may unsubscribe and
resubscribe to the same in-flight attempt without issuing a second GET.

Keep state adoption in each game screen. Difficulty and category restoration, form and
selection cleanup, focus, feedback, scoring, new-game mutations, and every server-authored
payload remain game-specific.

Preserve the two existing policy families during this refactor. Alchimie, Cald sau Rece,
Conexiuni, and Lanțul Cuvintelor discard terminal GET states and forget the active ID after
any GET failure. Intrusul and Perechi adopt terminal GET states so their score effects run,
forget only a 404 ID, and retain the ID with their existing retry message after a transient
failure. A later reliability change may unify these policies after separate product and
browser coverage; this extraction does not choose that behavior implicitly.

## Context / why

Each screen had its own copy of the same mount-time asynchronous sequence. The copies had
drifted in terminal and transient handling, loading state, and Strict Mode comments, while
mixing those lifecycle mechanics with meaningful game-specific reset and feedback code.
Changing those differences inside an extraction would make a refactor silently alter
score recovery and session retention.

The old ref guards also allowed the first request to update state after a real unmount so
that Strict Mode's simulated cleanup would not cancel the only request. A reusable
single-flight attempt with per-effect subscriptions preserves the one-request property and
lets a real cleanup suppress stale state, feedback, and loading delivery.

## Consequences

Async behavior tests cover no saved ID, live resume, both terminal policies, 404, both
transient policies, Strict Mode resubscription, and real unmount. The two source-level
resume assertions they replace no longer depend on a screen's local statement order.

This is a frontend-only refactor. Server sessions retain the 7,200-second sliding TTL,
1,000-entry per-game cap, per-entry locks, deterministic selection, and private answers.
API shapes, scoring formulas, content, accounts, and deployment behavior do not change.
