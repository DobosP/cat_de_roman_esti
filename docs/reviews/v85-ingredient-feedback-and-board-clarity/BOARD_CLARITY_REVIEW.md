# V85 exact source-label correction

Valid until: the bound source record, correction policy or derived content changes — then treat as history.

This is the implementing agent's authored review, awaiting separate review before application.
The proposed byte-bound edit is [board-label-candidates.json](board-label-candidates.json).
It repairs predicates under rubric A3/B1 without changing status, groups, order or inventory.

## Exact scope

| Source/group | Existing label | Reviewed proposal | Reason |
|---|---|---|---|
| `cx_gastronomie_171/g3` | Alb, sărat, din zona laptelui | Produse lactate | Brânză, Telemea, Urdă and Brânză cu smântână are dairy products; salt and white color are not universal properties of this group. |
| `cx_gastronomie_171/g1` | Localitatea e deja în meniu | Denumiri cu trimitere geografică | Varză a la Cluj, Covrigi de Buzău, Baclava dobrogeană and Bucovina gastronomică contain geographical references; the last two refer to regions, not localities. |

The source's complete before-record canonical SHA-256 is
`baf8750543974819f7d65cf6d3b7f09a00c2117c7448c71aeaefb7b107e9ab56`;
its exact after-record SHA-256 is
`e6a28e3f206ed295a3019c30876349efec1e409359df42daee45a397c2f189e9`.
Canonicalization is sorted-key compact UTF-8 JSON, without a trailing newline.

The g3 label names one consistent relation: each member is a dairy product. It does not
repeat a member name. The g1 label names a property of the denominations, including the
regional adjective, rather than pretending that the regional cuisine concept is a dish.
Neither repair adds a new hidden partition or an exclusive-origin claim.

## Factual basis and limitations

[DEX and DLRM's Urdă entry](https://dexonline.ro/intrare/urd%C4%83/59516) describes the
milk derivative made from whey and its sweet, soft form. The existing graph description
also explicitly calls it sweet cheese. Telemea is salty, but extending that characteristic
to all the other members makes the original hint false.
[DOOM's Dobrogea entry](https://dexonline.ro/intrare/Dobrogea/141324) identifies a region;
[the encyclopedic Bucovina entry](https://dexonline.ro/definitie/bucovina) identifies a
historical province. These support the wording correction, not a new claim about the
exclusive origin of a recipe.

This narrow review does not certify every existing source group or eliminate the source's
other editorial debt. In particular, the regional-cuisine meta concept and the old grill
group remain as authored. Their stock status is unchanged. No new pending item is promoted.

## Served effect and identity preservation

The source has three frozen Intrusul children and no Perechi child. Only
`vi_1535ff1ac283061d41a1` uses the repaired dairy label: Telemea, Urdă and Brânză versus
Covrigi de Buzău. The other two Intrusul payloads remain exact. All 153 Perechi rows remain
exact. There is no gastronomic Perechi shelf to claim as improved by this repair.

The Conexiuni source is approved but currently not pilot-eligible. Its two stored labels
are repaired without widening eligibility. The immediate player-visible gain is therefore
one served Intrusul hint and solution label; the g1 correction is source-only.

The offline authoring path uses the shared verified file rollback helper and binds the
whole approved source record. Missing/duplicate IDs, modified members or tile order,
unexpected labels, a partial correction and repeat application all fail before mutation.
The generated catalog and runtime loader both use the same exact source/member/label
identity policy. For hashing only, the repaired label maps back to its historical text;
the complete source record must be either its bound before or complete after state.
Served payloads retain the corrected text. This preserves candidate IDs and the frozen
diversity cap's tie ordering, avoiding unintended board replacement from a wording change.

Apply with `scripts/apply_pack_label_corrections.py --write`, then regenerate the existing
ranking and derived-catalog sidecars through their supported builders. Until regeneration
and the normal trusted-digest update, the runtime's artifact bindings continue to fail closed.
The release transaction is coordinated by the root session; this worker has not applied it.

## Verification performed before application

`PYTHONPATH=. ~/work/cat_de_roman_esti/.venv/bin/python -m pytest tests/test_v85_board_label_corrections.py tests/test_v38_derived_rankings.py tests/test_v38_ranked_catalog.py -q -o addopts=''`

**53 passed in 12.17 seconds.** The 20 new cases cover the exact source delta, invalid and
partial bindings, no-op dry run, successful mirrored write, validator failure, interrupted
second write with both mirrors restored, shared generator/runtime identity, and rejection
of a rebound but unreviewed source or stale derived label. Generated before/after documents
differ in exactly one display label among 336 rows. One hundred seeds per game/filter and
30 daily dates per game retain identical selected IDs or identical empty shelves.

An Intrusul API journey confirms the repaired label stays hidden initially, appears only
after the earned hint, survives the scored win and resume, and never exposes the answer
before the existing terminal boundary. Session TTL, entry cap, request bound, history and
scoring code are unchanged. An initial test assumed a nonempty gastronomic Perechi shelf;
it was corrected to verify the actual unchanged empty shelf before the green rerun.
