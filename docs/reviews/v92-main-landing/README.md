# V92 main landing

Valid until: a later main landing changes these inputs — then treat as history.

Verified: 2026-09-15. The owner's request to land the completed work covers all three
V92 sessions. Main advances from `6208eae` through ten implementation commits to
`d52f4b4`; the closure commit adds documentation and preserved evidence only.

V92 rebuilds Alchimie's tap/drag workbench, makes failed experiments free, and adds
persistent exploration with 225 concepts, 294 recipes, 121 craftable discoveries and
32 optional goals. Four earlier saved-book generations remain supported. The other
five games gain simpler controls and 92 reviewed rounds/targets: Conexiuni 6, Cald sau
Rece 13, Lanț 16, Intrusul 31 and Perechi 26. Shared KG vocabulary remains unchanged.

## Verification

The [landing receipt](verification.json) preserves the new constrained Python 3.14.6
results: [1968 backend tests](backend314.log) and [53 account tests](accounts314.log).
Both content validators and Ruff also pass under 3.14. The previous exact-input
[integration receipt](../v92-session03-vocabulary-and-interface/verification.json)
retains 1968 backend/53 accounts on Python 3.12, 212 native frontend and 480 browser
checks, with lint/typecheck/build green at 119.22/120 KiB initial gzip.

An independent read-only audit verified 400 current and archived SHA bindings with
zero mismatches, including final catalog approval chains and GUI/runtime inputs.
The previously scratch-only [Perechi log](../v92-session03-vocabulary-and-interface/perechi-recheck.log)
is now preserved at its exact already-recorded hash, along with 22 older logs still
referenced by the earlier V92 verification receipts. Every copied log matches its
existing verification hash. The discovery-world lint log uses lossless gzip to retain
its original trailing blank line without failing the staged whitespace gate. Both
encoded and decoded hashes are recorded. The status review link is repaired.
Earlier receipts describe their original pre-landing state; this record supersedes
their Python 3.14 and local-main limitations without changing their evidence.

## Publication and cleanup scope

This receipt is written after the implementation fast-forward and before the main
push; GitHub Actions records the subsequent remote CI result. The landing publishes
main under the owner's request and ADR-0004. Cleanup is limited to the three verified
V92 branches/worktrees and matching scratch directories, after checking remote main
and ancestry. Previews on ports 8150 and 8160 now run from main. Each passes six
read-only route checks and serves a JavaScript asset byte-identical to main.

Production remains the anonymous V91 deployment. No deployment or further creation
session is part of this landing. Human enjoyment and physical-device acceptance
remain separate from the automated/browser checks.
