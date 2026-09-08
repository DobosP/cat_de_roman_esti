Valid until: any reviewed source binding changes or V88 is superseded — then treat as history.

# Independent V88 Lanț recovery review

**Accepted; no blocking findings.** This review covers the Lanț server hint retention,
shared action owner, Contexto rename, Lanț screen/API and their focused tests. The exact
11-file source set and ten unchanged dependencies are bound in [lant-review.json](lant-review.json).

The move, undo, hint and manual-verification handlers acquire one synchronous ticket before
React can render again. The still-current ticket must own the same saved pointer before POST
and after each await. An uncertain mutation makes one read while ownership remains valid;
the helper has no mutation callback and cannot replay an action. Failed reads retain a visible
GET-only retry and lock mutation controls. Foreign pointers enter explicit saved resume, and
verified 404 cleanup removes only the owned pointer. Unmount, new-game attempts and saved
adoption invalidate old tickets; a stale finally cannot unlock a newer operation. Two null
storage observations preserve local-only play.

A recovered win uses the existing authoritative score and completion receipt. Recovery adopts
the complete position and earned help; neutral copy does not invent a lost move's progress or
correction verdict. The recorded browser journeys cover a single completed score, no POST
replay, failed verification, late wins/404, navigation and a preexisting foreign pointer.

The server stores one already-earned hint for the current position. GET never computes help
or advances its stage. Accepted movement, real undo and wins clear the payload; rejected moves
and undo at the start preserve it. The original three-stage computation is AST-identical after
removing only the response-retention wrapper. Alternatives remain capped at two named choices;
the terminal reveal remains one hop. Stage cap 3, move cap 64, 7,200-second sliding TTL,
1,000-session maximum, per-session locking and 64 KiB request limit are unchanged.

The response and session share a generated dictionary, but reviewed writers only replace or
clear it. They never modify its nested content. Construction and reads run under the same
session transaction; a later replacement cannot mutate a prior response after lock release.
The configured JSON renderer does not mutate these objects, and HTTP clients get decoded
copies. Future in-place payload writes would require revisiting this conclusion.

I independently verified that the shared helper, declaration and Contexto consumer are exact
after identifier substitutions. Seven existing Lanț runtime functions/classes and ten supporting
files also remain exact. All 11 source bindings and 16 lossless archive bindings match actual
files. The archived logs confirm **80 targeted backend tests, 193 native tests, 20 initial
browser cases and four later settled screenshot cases passed**. Initial directory mistakes and
screenshot adjustments remain disclosed in the builder's [verification](lant-action/verification.json).
I did not repeat heavy tests or perform independent visual inspection.

This is a source/evidence review, not human playtesting or the parent version's full integration
approval. Saved-pointer ownership remains a browser guard; it does not establish distributed
exactly-once behavior. No production, fixture, static asset or implementation file was changed
by this review.
