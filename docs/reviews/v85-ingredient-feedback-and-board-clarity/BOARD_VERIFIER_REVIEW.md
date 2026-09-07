# V85 board-label independent verification

Valid until: the bound candidate, correction implementation or relevant source record changes — then treat as history.

Verdict: **accept the exact two-label correction**. Reviewer `v85_ingredient_research`
did not author the board correction or its implementation. This verifies the narrow
existing-stock wording repair; it is not a promotion of the source or a certification
of its other groups. Exact file hashes are in `board-verifier-review.json`.

## Factual challenge

`Produse lactate` truthfully covers Brânză, Telemea, Urdă and Brânză cu smântână.
The old universal salt claim fails for sweet whey cheese. The independently opened
[Urdă dictionary entry](https://dexonline.ro/intrare/urd%C4%83/59516) identifies the
milk/whey derivative. The correction also avoids making whiteness universal.

`Denumiri cu trimitere geografică` covers the displayed names containing Cluj, Buzău,
the adjective dobrogeană and Bucovina. The independently opened
[Dobrogea entry](https://dexonline.ro/intrare/Dobrogea/141324) and
[Bucovina entry](https://dexonline.ro/definitie/bucovina) confirm the regional senses.
The replacement deliberately promises a property of the names, not that all four
are dishes or towns. It makes no exclusive-origin assertion. Neither new label
literally gives away a complete member name.

This source remains approved but outside the current pilot-eligible Conexiuni pool.
Its broader meta-concept and group-quality limitations remain. The g1 repair is
source-only. The served gain is exactly one Intrusul dairy hint/solution label:
`vi_1535ff1ac283061d41a1`. No Perechi improvement or new board is claimed.

## Refute-first implementation review

The before-source canonical digest was independently checked against actual Git
baseline `39b64cb`, not reconstructed from the proposed correction. The candidate's
policy hash matches the actual implementation. The expected after-source digest
also matches. Comparing complete before/after pack objects shows precisely the
two labels changed; all other records, statuses, members and order fields remain.

The write path binds the complete approved source, so a matching ID alone does not
permit a custom source. The before and complete-after states are recognized, while
missing/duplicate source IDs, mixed states, reorderings and unknown labels fail.
Reapplication refuses before writes. Additional independent mutations to category,
difficulty, title, description, ID, status, groups, group labels, order and an extra
unreviewed field were all rejected.

For identity hashing, the label fold requires the canonical source ID, supported
game, exact repaired label and a unique member subset of the recorded group with
the correct cardinality. It does not mutate the displayed payload. This helper is
not a standalone authorization boundary: both actual entry paths validate the
complete source record first. The runtime then validates payload group membership,
source label and intruder custody before checking its normalized candidate ID.
An attacker cannot merely rebind the outer artifact digest to bypass these source
and payload guards. Runtime custom source overrides retain their previous refusal.

The generator's source binding occurs before candidate generation and diversity
capping. Consequently label normalization preserves historical IDs and tie order,
while only the live label changes. The generated before/after catalog comparison
covers all 336 rows and shows exactly one label difference. Source sets, partitions,
IDs, order, ranks, eligibility and all 153 Perechi rows are identical. The three
Intrusul children of this source remain the same three boards.

The transaction snapshots both mirrors before any write, requires initial byte
identity, writes through atomic file replacement and catches `BaseException` for
verified rollback. Validator failure and interruption after the first mirror write
restore both original byte strings. It is an offline coordinated transaction, not
a concurrent live pack hot-update mechanism. Runtime sidecars must still be rebuilt
and their trusted digests updated before integration acceptance.

## Verification

Independent run:
`PYTHONPATH=. /home/dobo/work/cat_de_roman_esti/.venv/bin/python -m pytest tests/test_v85_board_label_corrections.py -q -o addopts=''`

**20 passed in 5.32 seconds**, plus the 10 independent field-mutation probes above.
The focused tests include full-record guards, duplicate/missing IDs, mixed/repeated
corrections, custom-source rebinding, stale payload label rejection, dry-run byte
preservation, mirrored writes and rollback under validator/interrupt failures.
One hundred seeds per game/filter and thirty daily dates per game preserve selected
IDs or the same empty shelf. The direct API journey retains answer privacy, exposes
the corrected clue only through the existing hint boundary, scores the win and
preserves the solution after resume. No runtime session or scoring state changes.

No blocker found in this exact scope. No full suite was run by this reviewer.
