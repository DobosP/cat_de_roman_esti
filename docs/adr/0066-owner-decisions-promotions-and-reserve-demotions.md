# ADR-0066: V42 owner decisions — 18 promotions and 67 reserve demotions

- Status: accepted
- Date: 2026-07-30

## Context

ADR-0065 left two owner queues: 18 gate-`keep` boards held only on the ADR-0019
near-duplicate boundary, and 67 verified sweep `demote` proposals on served boards. The
owner decided (2026-07-30): approve all 18; demote the structural kills — and triage showed
every one of the 67 verified proposals carries a structural kill (exact quad re-serves,
B5 mirrors, B3 partition breaks, B9 leaks, unverifiable content), so the full set demotes.

## Decision

1. **18 promotions** applied as status flips (`pending` → `approved`). Promotion exposed one
   real defect the pending pool had masked — `cx_gastronomie_298` carried a duplicate tile
   (approved-only playability checking) — fixed before landing.
2. **67 demotions** applied via the ADR-0055 reserve model, NOT status flips: the boards stay
   `approved` but a new committed sidecar, `cat_de_roman_esti/fixtures/board_demotions_v43.json`,
   excludes them from `pilot_eligible` in `scripts/rank_games_pack.py`. Rationale: a status
   flip broke runtime invariants (derived-catalog sources must stay approved) and the reserve
   model is the established never-selected mechanism. Un-demoting or revising is an owner
   edit of that sidecar plus re-rank.
3. **Derived catalog stays frozen** (ADR-0054): the generator now hardcodes the V38
   123-source snapshot (`_V38_SOURCE_SNAPSHOT`) and the runtime loader validates sources as
   *approved* rather than *currently eligible* — freeze-time eligibility is bound by the
   catalog digest pin; live eligibility churn no longer invalidates the frozen children.

## Consequences

- Served pool: **450 zero-FAIL boards** (Conexiuni 76, Cald sau Rece 202, Lanț 94,
  Alchimie 78) — leaner and structurally clean; approved 603 / pending 222.
- The demotions emptied **11 Conexiuni shelves** (arta_cultura ușor+greu, film_tv ușor,
  sport ușor+normal, societate ușor+greu, gastronomie/geografie/personalitati/știința
  normal) — hidden by the picker per ADR-0058, no dead ends. These are the next authoring
  wave's targets; the recycled-quad heartland (Enescu/Caragiale/rivers/lakes clusters) is
  exactly where fresh boards are needed.
- Two pinned daily assignments re-picked deterministically (previous winners demoted).
- All content tripwires (pack digest, counts, reports, artifact, empty-shelf set, dailies)
  moved deliberately with this ADR.
