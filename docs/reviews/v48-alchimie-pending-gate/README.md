# V48 Alchimie pending-pool quality gate

_Reviewed and closed 2026-08-01. This report records the evidence for ADR-0072._

## Scope and release bar

V48 freshly reviewed all 21 pending Alchimie records against the current E1–E5
rubric. The sorted exact ID set has SHA-256
`d7cbc45ce53f4c70e2d3c3d8214e5f49964422f703f3004514ab08eccb822120`.
V42 judgments were history only and were not reused.

The quota-free release bar required recognizable and useful seeds, at least two
semantically intuitive live openings, a short inferable target route, no free answer,
and bounded choice. Two independent promotions were required to ship; either rejection
rejected; mandatory ADR-0019/A5 cases stayed pending for owner disposition. Both
reviewers bound every judgment to the same source-bound live-projection artifact,
SHA-256 `486aa09129e6ad1e4b4477b4721782ee7e041c1e3329714d82897ccb9757571c`.

## Broad-graph versus live-recipe evidence

The deterministic critique reported **0 FAIL** records and only **3 WARN** records:
Subtitrare and Subcarpații were below the normal salience floor, while Uniunea Europeană
was below the ușor floor. That result describes the broad source graph, not the private
sparse recipe book that a player receives.

Across the 21 dossiers, broad graph traversal reported 158 productive seed pairs, at
least three per board. The runtime projection retained only 50 target-useful openings.
Seven records therefore have only one live opening and fail the literal E2 floor:

- `al_arta_cultura_015`
- `al_geografie_032`
- `al_limba_047`
- `al_personalitati_070`
- `al_viata_de_roman_092`
- `al_viata_de_roman_094`
- `al_viata_de_roman_095`

The projection audit archives every source record and binds its record digest, dossier
binding, source pack, KG, rubric, runtime sources, and generator. For all 21 records,
declared par equals exact par and projection par; route, recipe-pair, projected-concept,
and results-per-pair bounds all pass. Those structural bounds do not override semantic
E1–E5 failures.

## Two independent E1–E5 reviews

`Graph/live` is the dossier's broad productive-opening count followed by the actual
runtime opening count. The failure column records the synthesized strict basis; A5 is an
owner hold rather than a quality pass.

| Board | Graph/live | Analyst | Verifier | Final | Strict basis |
|---|---:|---|---|---|---|
| `al_arta_cultura_015` | 13/1 | reject | reject | reject | E1/E2/E3: filler and one arbitrary taxonomy route |
| `al_film_tv_022` | 12/5 | reject | promote | reject | E3: Film + Televiziune does not distinguish Subtitrare |
| `al_gastronomie_026` | 7/4 | keep | keep | keep | A5 hold; E1/E3 quality kill, every route uses Țuică |
| `al_gastronomie_030` | 4/2 | keep | keep | keep | A5 hold; E3 quality kill, every route uses Vin fiert |
| `al_geografie_032` | 7/1 | reject | reject | reject | E1/E2/E3: only cătun + pârâu opens the board |
| `al_limba_047` | 5/1 | reject | reject | reject | E1/E2/E3/E5: filler and one six-action taxonomy route |
| `al_literatura_051` | 5/3 | reject | promote | reject | E1/E3: unused seeds and a generic setting target |
| `al_literatura_097` | 15/3 | promote | promote | promote | Clean E1–E5: six coherent seeds, four short routes |
| `al_muzica_065` | 9/4 | reject | reject | reject | E1/E3: no Cargo-specific ingredient identifies Ploaia |
| `al_personalitati_070` | 5/1 | reject | reject | reject | E1/E2/E3: unsupported sole opener and filler |
| `al_societate_076` | 10/3 | reject | promote | reject | E1/E3: generic civic taxonomy and unused seeds |
| `al_viata_de_roman_092` | 6/1 | keep | keep | keep | A5 hold; E2/E3/E4 quality kill, every route uses Țuica de casă |
| `al_viata_de_roman_094` | 6/1 | reject | reject | reject | E1/E2: one live opening |
| `al_viata_de_roman_095` | 3/1 | reject | reject | reject | E1/E2/E3: filler and an arbitrary six-action route |
| `al_viata_de_roman_098` | 9/2 | reject | reject | reject | A6/E3/E4: target is a recycled, arbitrary sibling game |
| `al_viata_de_roman_099` | 7/3 | reject | reject | reject | A6/E1/E3: template reskin, filler, and `+ușă` magic |
| `al_viata_de_roman_100` | 7/3 | reject | reject | reject | A6/E1/E3: template reskin, filler, and `+ușă` magic |
| `al_viata_de_roman_101` | 7/3 | reject | reject | reject | A6/E1/E3: template reskin, filler, and `+ușă` magic |
| `al_viata_de_roman_102` | 7/3 | reject | reject | reject | A6/E1: repairable school route inside a filler reskin |
| `al_viata_de_roman_103` | 7/3 | reject | reject | reject | A6/E1/E3: filler reskin and loose final craft |
| `al_viata_de_roman_104` | 7/2 | reject | reject | reject | A6/E1/E3: filler reskin and `+ușă` magic |

The gameplay analyst returned **1 promote / 17 reject / 3 keep**. The independent
verifier returned **4 promote / 14 reject / 3 keep**; its extra promotions were
`al_film_tv_022`, `al_literatura_051`, and `al_societate_076`. Conservative synthesis
resolved all three disagreements to reject and produced the final
**1 promote / 17 reject / 3 A5 keep** result.

## Survivor factual checks

`al_literatura_097` is grounded beyond graph closure. Făt-Frumos is the protagonist of
_Tinerețe fără bătrânețe și viață fără de moarte_ in the
[school-hosted text](https://educatie.inmures.ro/fileadmin/galerii_foto/institutii/pdf/tinerete_fara_batranete.pdf)
and is independently identified in the
[Liceunet character overview](https://liceunet.ro/petre-ispirescu/tinerete-fara-batranete-si-viata-fara-de-moarte/personaje).
The zmeu conflicts behind the other opening family appear in the source texts for
[Greuceanu](https://ro.wikisource.org/wiki/Greuceanu) and
[Prâslea cel voinic și merele de aur](https://ro.wikisource.org/wiki/Pr%C3%A2slea_cel_voinic_%C8%99i_merele_de_aur).

## Applied outcome and digests

- `al_literatura_097` was promoted; 17 rejected records were removed; the three
  alcohol-dependent A5 holds remain pending and unserved.
- Alchimie is now 82 records = 79 approved/selectable + 3 pending. Its ID high-water
  mark remains 106. The full original-game pack is 618 records = 610 approved + 8
  pending, with 449 pilot-eligible records.
- The 79 approved Alchimie sparse projections have canonical digest
  `50f82c4660c54708e00cdd31e28c68a60034c83444a2a9dd2d5cc879500c2683`.
- Applied pack SHA-256:
  `05e80ab2ffb8ec185ad445305a728c784a93e683474d5ec645c10aa1247184ed`.
- Rankings SHA-256:
  `0e2b5cda2c46d81f9b5a5cc2a274a7a55bf387a203bae3df48b1b5c2d1bde219`.
- Derived-catalog SHA-256:
  `87544c899799e92ea8733303ab0ed286650abfe0298008a38bcbc7aef75d5ae2`.
  Its frozen 336-board payload remains 183 Intrusul / 153 Perechi with SHA-256
  `71a2acefb7e0ec62da32ad2645238d73d5e83375808160c0bd1800febd3a73b6`.

No graph, KG, alias, node, edge, or new board was added. Frontend behavior, hidden
answers, deterministic sessions, the 7,200-second session TTL, and the 1,000-session cap
are unchanged. V48 did not deploy.

## Archive and replay

Machine evidence consists of `critique.json`, the 21 exact files under `dossiers/`,
`projection-audit.json`, and `alchimie_verdicts.json`. Their SHA-256 digests are,
respectively:

- `1790609fd54bb94bc61719f909940a6414f8c9ae9612252100de5abc5482deb2`
- dossier manifest
  `2a3250f1701ba54ee586670979d4105a5d6b093e7b2227cb0230bbd721d723db`
- `486aa09129e6ad1e4b4477b4721782ee7e041c1e3329714d82897ccb9757571c`
- `e14ceab934c7e19ce8a2f1a2cdcf9e03650654e5ae268fa6e04f51401368b8d7`

The audit is bound to pre-apply pack SHA-256
`c4542d4201c45b04f58563eb08aa2ba0973389f453f5181f53066a88df550d05`,
KG SHA-256 `f2a4229c05072028fef1d8e68e97a6fe2e7c74c535bcca0fca0a0708acf5ed12`,
and rubric SHA-256
`29781ef5daa65b0637425ea258702f9f644486807ea61e49020be66d168e0ca3`.
Its runtime-source manifest is
`0d38a914e4b8fc5d0730d1fc1bf23530214b1112ec2101218d4951050bf126ea`,
and its generator SHA-256 is
`9dcae3ce7e5d4643fced7edcf6d962cc55568163fa5d77c93a325b69aeb405c2`.
Its embedded `source_record` rows preserve all 17 removals because Alchimie has no
generic rejection ledger.

On that exact pre-apply source, `scripts/audit_alchimie_projections.py` rebuilds the
source-bound private recipes, and this command applies the bound verdicts transactionally:

```bash
python scripts/apply_rereview.py \
  --dir docs/reviews/v48-alchimie-pending-gate
```

Tampered runtime sources, generator, dossiers, source rows, or reviewer audit bindings
fail closed. Replaying against the post-apply pack is intentionally rejected because the
promoted and removed records are no longer pending.
