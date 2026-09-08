# V91 migration and history audit

Valid until: a bound source, test, input or content artifact changes — then treat as history.

Reviewed 2026-09-08 by `v91_migration_audit`, independently of the migration author.
**Accept: no actionable findings in this bounded audit.** The review covers the
seed-only writer, its tests, the V91 historical inverse, the narrow V90 test
normalization, current content pins and the bundled derived-catalog digest.

The migration can replace only the frozen ordered seeds of `al_sport_083`. Its
full before/after record digests, whole baseline pack, unchanged KG/runtime/rubric
inputs, candidate dossier and profiles constrain the write. Both distinct
reviewers must accept those exact inputs. It rebuilds the live dossier and private
recipe book, checks all six initial seeds and four openings, and compares the full
reviewed initial profile. The approved status remains unchanged.

Dry run writes nothing. The explicit write checks both mirrors, validates both
resulting packs and uses the existing transaction's verified restoration on
failure. Tests cover missing or unbound reviews, copied reviewer identities,
tampered inputs, expanded proposals, stale sources, mismatched mirrors, rebuilt
content drift, interrupted writes, validation failure and reapplication.

The V91 inverse verifies complete current and restored artifact hashes before
earlier history is checked. The V90 test now compares its stock-preservation claim
at the V90 boundary; its V89 reconstruction pins remain intact. Independent
comparison with baseline `e2e03638b90fc9248c33f70eedaa8c9c5fbd87ad` confirms:

- Only `al_sport_083` changes among 661 pack records; no record is added or removed.
- KG and mobile artifacts remain byte-identical. All 336 derived boards remain exact.
- The regenerated ranking moves Sport 083 from rank 38 to 23 and shifts 15 other
  ranks by one. Its pilot score rises 67 to 70 and weight rises 3 to 4;
  `al_limba_042` crosses the weight boundary from 4 to 3. No other score changes.
- The sole derived runtime edit is its bundled hash, matching the regenerated
  catalog. Existing freshness enforcement remains intact.

The first targeted run passed **85 tests**: 37 writer, 7 V91 history, 33 V90 graph
and 8 V89 content cases. A separate collection confirms those counts. No tests
failed or were skipped. The command, 29 exact source/evidence bindings, artifact
comparisons and deterministic compressed raw logs are in
[`migration-audit.json`](migration-audit.json).

This is an integration audit of the accepted candidate; factual and player-quality
judgments remain the separate bound reviews. The migration is a serial offline
operation. Complete release gates and local landing remain with the root session.
Three older Neagu labels remain unchanged as explicitly excluded from this repair.
V91 is the final authorized version; stop after its local landing.
