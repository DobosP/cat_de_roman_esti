# V90 final integration and hash audit

Valid until: a bound input or reviewed file changes — then reassess before landing.

**Accepted. No blocking findings.** The immutable
[audit input manifest](audit-input-manifest.json) has SHA-256
`bd0fe88b82a6a9f716b2084c78e8d828b407dcc295a171ee7aa8b781ce2e65db`.
All 320 present hashes and 14 deleted baseline blobs match. Coverage includes the complete
delta from `190d7fd`, including the committed kickoff; only the explicitly named audit
and final-manifest files are outside this input snapshot.

All **1,635 protected inputs** match the integration freeze. No new runtime/test/rubric
source escaped that freeze; later additions are review evidence. All **16 passing gate
receipts** have exit 0, matching command/directory, raw and gzip hashes/lengths, zero gzip
timestamps and exact recorded tails.

- Python 3.12.3 and 3.14.6: **1,608 backend tests each**.
- Accounts: **53 tests each**.
- Frontend: **193 native tests and 246 browser checks**, with zero browser retries.
- Initial JS/CSS gzip total: **118.88 KiB**, below the 120 KiB gate.
- Fixture, pack, pending critique, lint, typecheck, build, docs and whitespace gates pass.

The first Python 3.14 process is preserved separately with observed exit 143 and no
pytest completion summary. It is excluded from passing gates. Its archived frozen inputs
are identical; the successful rerun uses the same pytest command. An exact runner
comparison shows only periodic progress monitoring changed. The cause of the interrupted
run remains unestablished; no timeout, memory issue or test failure is inferred.

Local main was clean at `190d7fd` when checked; V90 had not been merged. This audit ran no
tests, builds or research and changed no protected source or prior evidence.
[The exact audit receipt](FINAL_INTEGRATION_AUDIT.json) records all verified gate hashes
and coverage. The orchestrator must bind this new pair and the immutable input snapshot
into the final manifest, complete the final docs/whitespace check, and recheck reviewed
state and owner instructions immediately before the authorized local landing.
