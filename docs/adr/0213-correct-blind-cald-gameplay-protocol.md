# ADR-0213: Correct the blind Cald gameplay protocol

Date: 2026-10-25
Status: accepted; independent cap-eight code and real-output verification passed

## Context

The qualified workflow helper required `ambiguous=false` in a pre-feedback opening response.
At that point the critic cannot know the hidden target, so the field described epistemic
uncertainty rather than puzzle or target-sense ambiguity. Rejecting that field cleared five valid
committed openers and fabricated distinctness and replacement failures. The public challenge also
omitted `difficulty` and `board_category`, although native Cald exposes both before guessing.
Historical B12 still has real cold-opening, wrong-target and final-ambiguity failures.

## Decision

- Introduce a separately versioned helper bundle and opening response schema 2 with exact keys
  `schema`, `challenge_id` and `openers`. Pre-feedback target knowledge is unassessed. Final target
  and dominant-sense ambiguity remains an honest required boolean and must be false to pass.
- Publish only exact SHA-bound native `difficulty` and `board_category`. Target, board identity,
  source, graph data, neighbours, clues, examples, authored guesses and private fields stay sealed.
- Validate schema, identity, opener shape, normalized distinctness, event equality, chronology,
  receipts, final target/sense and warmth independently. A separate failure never discards valid
  opener bytes or invents substitutions. Legacy schema-1 ambiguity is diagnostic epistemic metadata.
- Exclusively persist the exact full comparator result before local expectations run. Keep native
  dispatch/delivery/read/action and first-key-access evidence as separate required proof.
- Preserve exactly five critic-chosen pre-feedback openers, at least one of those same five at raw
  distance at most two, adaptive cap eight, unique actual target match, natural unambiguous dominant
  target sense, and all M4/native/review/source/corpus/HTTP/fuzzy/pin gates. The builder accepts only
  exact integer 8; direct oracle use and comparison fail unless the sealed key and public limit also
  carry exact integer 8. Five opening turns plus eight adaptive turns means turn 14 is refused.

## Consequences

B12 remains an immutable historical FAIL; its improved regression diagnostics are cold opening,
wrong target and final ambiguity. Independent GP2 review rejected `gameplay-protocol-v3` because
its caller-selected adaptive limit admitted 1–100. The separate `gameplay-protocol-v3-cap8`
correction is a GP3 checkpoint; the rejected helper's passing suite cannot qualify its changed
bytes. This checkpoint grants no content approval, installation or production use. A fresh
independent code review, real-output verification, full-suite qualification, manifest and exact
separate pin remain mandatory before the successor helper can be used.

## Qualification record

The corrected frozen version passed fresh independent exact-code review and 103 current-byte regressions with no skips. The original rejected helper and B12 verdict remain unchanged. Production use of this local helper requires its separate immutable version manifest/pin; this record grants no content, target, installation or landing approval.
