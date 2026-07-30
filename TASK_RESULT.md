# Task Result — V44 common-word Contexto quality wave

## Outcome

- Repaired Cald sau Rece feedback for all 71 shipped V30–V33 inbound-only common-word
  nodes through 26 explicit mature scoring anchors without changing graph topology.
- Added 12 unanimously safe resolver aliases and 11 non-winning projection terms;
  rejected ambiguous, disputed, and normalization-colliding candidates.
- Promoted `Capra cu trei iezi` and `Abecedar` from fresh bound C1–C6 dossiers.
- Reserved three later IDs that duplicate already-selectable Contexto targets. Runtime
  stock is now 201 selectable records with 201 unique targets.
- Unified guesses, typo help, suggestions, and warmer clues behind one effective scoring
  rule, closing proxy-to-secret disclosure and clue-rank mismatch defects found by the
  adversarial review.

## Files

- Runtime: `contexto.py`, `contexto_feedback.py`, `contexto_projection.py`.
- Content: mirrored KG/pack/ranking/derived artifacts and V44 reserve sidecar.
- Review: exact vocabulary funnel, two bound dossiers, unanimous verdict artifact.
- Contracts: ADR-0068, current status, mobile snapshot, and V44 regression suite.

## Verification

- Complete backend: 700/700 green.
- Accounts: 53/53 green; bounded session store: 16/16 green.
- Ruff, `git diff --check`, pack, KG, ranking, and derived-catalog validators: green.
- Adversarial 71-target API sweep: no typo leak, repeated clue anchor, or advertised/play
  rank mismatch.
- Pack: 608 approved / 220 pending; 447 selectable originals.
- KG: 2,364 nodes / 9,217 edges / 7,452 aliases / 180 puzzles.
- Frozen derived board payload: unchanged at 183 Intrusul / 153 Perechi.

## Risk

Contexto-only scoring behavior changes for the closed 71-node inventory. Exact wins,
public guess identity, session TTL/caps, shared graph routes, Lanț/Alchimie behavior, and
the frozen derived board payload are pinned by regression tests. No frontend files changed
and V44 has not been deployed.
