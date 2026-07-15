# ADR-0023: Two-layer content critique gate before approval

Date: 2026-07-15
Status: accepted

## Decision

No pack item reaches `status: approved` without passing the two-layer critique gate.
Layer 1, `scripts/critique_pack.py` (deterministic, committed): confusability-aware
tile fairness (type-compatible foreign pull, engine `_board_quality` parity as dossier
context), red-herring budget, mirrored-group detection, node_type coherence (3+1 /
2+2), duplicate-quad detection, per-difficulty salience banding, and member-overuse —
any FAIL blocks promotion (`--strict`). Layer 2, the judge fleet
(`.claude/workflows/critique-games.js`): Sonnet analysts hard-critique each item's
dossier against `docs/CRITIQUE_RUBRIC.md` (predicate honesty, unique partition,
recognition, Romanian social relevance, difficulty gradient), then Opus verifiers
adversarially re-judge with live web checks of Romanian-relevance signals (rubric
section D). The durable verdict contract is
`{"game": ..., "verdicts": {"<id>": "promote|reject|keep"}}` consumed by
`scripts/apply_rereview.py`; sweeps over already-approved stock emit
keep/demote/revise *proposals* only — demoting served content stays an owner decision,
and the ADR-0019 editorial boundary overrides any gate verdict in both directions.

## Context / why

The playability validator checks solvability, not quality: `_validate_conexiuni`
never reads labels beyond non-emptiness, `_validate_contexto` never reads
`difficulty`, and the mined-board fairness rule (`conexiuni._board_quality`) was
never applied to curated boards. Player-reported failures got through: approved
festival groups holding three festivals plus the village of Bonțida
(cx_meme_net_136/203 — a "3+1" type outlier), boards pairing festivals with their
host cities in 1:1 strong-edge correspondence plus a generic-abstraction group
(cx_muzica_271/206), the same four-member quad re-skinned across up to six approved
boards, and approved Contexto targets no Romanian free-associates to (Sonicitate,
salience 0.15; Meglenoromână; Pagaia din Deltă). The first full lint run found 127
type-compatible fairness FAILs and 689 duplicate/near-duplicate group warnings across
the approved stock. Why not extend `packs.validate_payload` with these checks: it fails the
whole CI gate on the *existing* served pack at once, conflates solvability with
editorial quality, and hard-coding judge-dependent judgments (recognition,
predicate honesty) into the runtime validator is impossible anyway. Why not an
LLM-only gate: not reproducible, and burns judge tokens on defects a deterministic
lint catches for free. Why not raw engine-parity fairness for curated boards: it
over-fires (208 vs 127) on type-partitioned boards (hosts + their shows) that play
fine because tiles of different types cannot be confused; the raw count is still
reported in dossiers. Judge fleets follow the fleet-skill routing (analyst critique
→ Opus adversarial verify, escalation not majority vote); prior verdict practice
(v16/v21) was scratchpad-only prose in STATUS.md — this ADR makes the contract
durable.

## Consequences

New content batches must ship `critique_pack.py --strict` clean and carry judge-fleet
verdicts before `apply_rereview.py` promotes them; import briefs should cite the
rubric so authors stop producing mirrored groups and type outliers at the source.
The approved stock now has a measured defect surface (216 FAIL findings) to be worked
through as owner-reviewed sweep batches; until then, served content is unchanged.
Thresholds (salience floors 0.60/0.35/0.20, strong-edge 0.6, mirror ≥3, red-herring
budget <4, overuse >8) live in `critique_pack.py` and should be recalibrated when the
graph's salience model changes. Unchanged: serving order and curated-first selection
(ADR-0011), playability floors (ADR-0015/0016/0018), hidden-answer boundaries,
session bounds, operationIds, and the ADR-0019 owner boundary.
