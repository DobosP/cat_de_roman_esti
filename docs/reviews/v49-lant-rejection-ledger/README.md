# V49 durable Lanț rejection-ledger audit

_Audited 2026-08-11. This report records the evidence for ADR-0073._

## Scope

V49 closes the workflow debt recorded by ADR-0069 and STATUS without re-reviewing or
changing a game record. The seed contains exactly the 104 V45 `reject` outcomes. The
three V45 `keep` outcomes remain pending repair holds and are absent from the ledger.

The machine summary is `seed-audit.json`. The durable output is
`cat_de_roman_esti/fixtures/lant_rejection_tombstones.json`; it contains only review
identity and provenance, never runtime boards.

## Seed recovery and binding

The 104 rejected source rows were replayed from pre-V45 commit
`246e8577412831405c67bfd6e8843121d8309cd0`. Every row was pending there. Its canonical
record digest, directed endpoints, dossier binding, and final reject outcome match the
V45 dossier and complete gate archive.

| Evidence | SHA-256 |
|---|---|
| Pre-V45 pack bytes | `742478415995b67379ba6fe58f939132abbff141aef7af392eff05b70e7845b6` |
| V45 verdict gate | `4e976a185b27ccee2737542ed8321c6664b7b8c974ae8e793076571964af4458` |
| Sorted rejected-ID set | `eadd0fc249c8bcdd601e2ffd9a03b0c2aa472e9115d853fdf165aa884bd597e6` |
| V49 ledger | `e3d8166aa5c59c2ff1e7cba06be4fcd505d02a8c98224ab2fe6126d6c826cc29` |
| V49 seed audit | `10fda097f8c91986db9ad14d3784be01977fbc90ff7cf889ae3f86d3b4726fb3` |

The ledger has 104 IDs and 104 unique directed pairs. No ID or directed pair overlaps the
current runtime pack. `lt_literatura_210`, `lt_stiinta_216`, and
`lt_viata_de_roman_211` are explicitly excluded.

## Quality conditions checked

V49 reviewed the previous-wave conditions before adding enforcement:

- universal A1–A7 and Lanț D1–D5 remain the content bar, including exact runtime
  distance/band validation, at least two credible first hops, no width-one shortest-path
  choke, recognizable endpoints, honest relations, discovery arc, and freshness;
- deterministic FAIL blocks promotion, WARN requires recorded human justification, and
  two independent promotions are still required; either rejection rejects, with no quota;
- the pending gate now compares each selected directed pair with every approved, pending,
  kept, unrelated, co-promoted, and same-batch-rejected Lanț row plus durable rejection
  debt; the row excludes itself by ID;
- candidate import checks the canonical post-alias directed pair before mutation;
- schema validation recomputes pair and initial V45 ID-set integrity; the V49 regression
  cross-binds every seed row's record, dossier, and gate digests to the V45 archive;
  future rejections compute those digests inside the pack transaction and roll back with
  it on validation failure;
- reverse direction is not inferred, and corridor similarity remains human D1–D5
  evidence rather than an unreviewed automated threshold.

## Unchanged boundaries

The package and test pack copies remain identical at SHA-256
`05e80ab2ffb8ec185ad445305a728c784a93e683474d5ec645c10aa1247184ed`.
Rankings remain `0e2b5cda2c46d81f9b5a5cc2a274a7a55bf387a203bae3df48b1b5c2d1bde219`;
the derived wrapper remains
`87544c899799e92ea8733303ab0ed286650abfe0298008a38bcbc7aef75d5ae2`.
The frozen 336-board payload remains
`71a2acefb7e0ec62da32ad2645238d73d5e83375808160c0bd1800febd3a73b6`.
KG, content statuses, rankings, runtime selection, scoring, sessions, accounts, frontend,
and production are unchanged.

## Regression contract

`tests/test_v49_lant_rejection_ledger.py` cross-binds the seed, V45 archive, exact pair
semantics, full-inventory critique, candidate preflight (including alias canonicalization),
future transactional append/rollback, non-runtime boundaries, pack mirrors, counts, frozen
derived payload, and the 7,200-second / 1,000-session limits.
