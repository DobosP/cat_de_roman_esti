# Independent V44 historical-scope correction review

Valid until: the bound test, helpers or artifacts change — then re-review.

Reviewed 2026-09-08. **Accept the isolated test correction; no review blockers.**
[Exact hashes and evidence](V44_REVIEW.json) bind the changed test SHA
`7b6a29497c76d9baa8d70cf034088c37133a1b0d61b5c9f659803cc401ae303d` and patch SHA
`33d7049f5dd30d0af8bf09eb7ee439a783681873d3c0b20d2008589ef5b91e08`.

The old assertion tested pre-V88 isolation against the current target set, which now
includes Mop. Mop already existed inside that old cleaning component. The correction
restores the exact V88 pack/rankings through reviewed inverses and requires exactly
235 distinct historical targets, with Mop as the sole current addition. It retains
all original isolation and bridge checks for those historical targets.

The independent current-target invariant remains complete: **all 236 eligible/unique
targets must be reachable from every proxy anchor**. The exact 71-proxy count and
mapping hash remain unchanged. Additional assertions require the same six cleaning
proxies to reach Mop in all three graphs: pre-V88, current and with the reviewed bridge
removed. Native Mop identity, zero self-distance and its existing Podea proxy remain
explicitly checked. No source behavior, topology, limit or old data pin was altered.

I compared the whole test module AST: after excluding the one revised function and
its two new historical-helper imports, the module is identical to baseline. I also
verified all 16 source hashes and five lossless evidence archives, including the exact
current patch. The [corrected receipt](history-tests/v44-topology-corrected.json)
records **110 passes in 18.67 seconds**, with Ruff and whitespace green. The
[initial reproduction](history-tests/v44-topology-initial.json) remains preserved as
one failure in 2.61 seconds. I did not repeat tests.

The original [final content audit](FINAL_CONTENT_REVIEW.json) retains its exact original
hash and pending-gate statement. This separate review closes only its requested narrow
test-review condition. Full corrected backend matrices and the final completed-receipt /
manifest audit remain required before local landing.
