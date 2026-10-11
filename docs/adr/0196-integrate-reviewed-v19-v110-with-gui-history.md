# ADR-0196 — Integrate reviewed V1.9/V1.10 with GUI history

Status: Accepted for source integration (2026-10-11); combined qualification NOT RUN.

## Context

The GUI review branch a58773f and local main6fbd7a4f8aab2003e8a9e2e8ed781c8aece94db3
(literal SHA read at merge time) diverged after3f327c6 (the ADR-0194 V1.8 merge
base). Main adds40 commits: complete reviewed V1.9 (seasons and school) and
V1.10 (everyday discovery) installations, their native reviews, installed
authorities, pins, bundle/digest and two independent1207-case HTTP corpora.
No main commit touches the trust set (`scripts/gate.sh`, `.gate.env`,
`compose.gate.yml`, `Taskfile.yml`), ADRs or GUI serving/build/gate code. Old
receipts on either side do not qualify the merged executable.

## Integration decision

Repeat the [ADR-0194](0194-integrate-reviewed-v18-with-gui-history.md) method with
a real merge commit of the literal main SHA. Main's content, pins, authorities and
native reviews win unchanged; nothing is regenerated, re-signed or re-approved.
[0189-behaviour-bound-installed-content-authorities.md](0189-behaviour-bound-installed-content-authorities.md)
still governs live combined content checks. This is a parent technical
integration under continuing work, not a new human content approval, reviewer
identity or GREEN qualification.

Textual conflicts were limited to `docs/STATUS.md`, `WORKLOG.md` and
`go-backend/internal/httpgolden/golden.go`. The GUI branch indexes reviewed
corpus sources once per process; main's `reviewedV19`/`reviewedV110` loaders join
that indexed list after `reviewedV18` in main's selection order. Every digest and
1207-case/eight-source check main added stays, and a match still returns a fresh
re-verified corpus.

## HTTP selector history

Keep the six earlier corpora, GUI0437 and V1.8 2c02 byte-exact. V1.9 3cce and
V1.10 bd72 are genuine distinct captures: each keeps every ordered request and
status of its predecessor and changes exactly23 bodies. The GUI V1.8 test kept
its literal identity, selection and refusals; like main's own superseded tuples
(V1.2 in95f94e3, V1.5 in902a341), its live-bundle clause moved to the current
version. New GUI selector tests bind V1.9/V1.10 bytes, digests, references and
tuples; V1.10 owns the live-bundle clause; all nine older tuples still select
their own responses; changed, missing, extra, nil, empty and all62 proper
V1.10/V1.9 and V1.9/V1.8 mixtures refuse before HTTP. No assertion is weakened.

## Qualification boundary

Combined unit and managed full remain NOT RUN at this source decision: Paul's
trust pin for the `.gate.env` change at the final tip comes first, then one full.
Focused/rail/validate/export results for the merged tree are recorded in the
[GUI handover](../GUI_MIGRATION_HANDOFF.md). Active size limits, physical Samsung,
formal M0/M1/KIT_BUMP/M2 and any UI activation/deployment authority stay open.
