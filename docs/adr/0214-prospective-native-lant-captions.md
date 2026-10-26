# ADR-0214: Produce source-bound prospective native Lanț captions

Date: 2026-10-26
Status: accepted as amended by ADR-0215–ADR-0218 and
[ADR-0219](0219-land-portable-prospective-captions.md), which corrects the producer-binding claim

## Context

M4 needs native player-visible Lanț captions for a prospective graph. The full serving export
correctly refuses that graph because reviewed catalog and ranking inputs still bind the baseline;
their refresh and independent approvals occur later. Rewriting those pins, copying the baseline
bundle, deriving captions in Python or changing stage order would weaken the source boundary.

## Decision

- Add an offline `cat-content prospective-lant-captions` command for explicit KG, pack and new
  output paths. It applies the existing strict fixture and pack validators and emits only an
  explicitly unapproved, non-serving Lanț caption artifact outside the repository.
- Share one native caption function between full serving `Build`, the public `Caption` operator and
  prospective generation. Baseline maps must match for every directed edge, including reviewed
  overrides and relation fallbacks.
- Bind exact producer KG, pack, rubric, frozen Unicode/rule inputs, Go 1.27.3 and complete native
  source inventory. Output is exclusive and refuses repository paths, existing files, symlinked
  source files and symlink-traversing output parents.
- Use a separately versioned blind-helper consumer. It requires an external expected artifact
  SHA-256 from retained native producer evidence, exact schema/game/input/native bindings and full
  prospective directed-edge caption coverage. Artifact provenance stays in the sealed private key;
  the public challenge contains only native gameplay context.
- Keep full export and every catalog, ranking, source, derived and rail validation path unchanged.
  The prospective artifact is never accepted as an installed bundle or approval marker.

## Consequences

The technical M3→M4 dependency can proceed without authorizing any content or weakening later
review. A changed artifact cannot be trusted by updating its own fields; the caller must supply the
separately retained producer digest. Missing captions, wrong schema/game/types, stale KG/pack/rubric/
rules/native bytes, invalid paths and unsafe overwrite attempts fail closed.

Author tests are implementation evidence only. Fresh independent exact-code review and native
verification remain required before this workflow is pinned, followed by a separately reviewed
content plan/input addendum before B13 gameplay resumes. Existing failed verdicts, budgets, holds
and all factual/quality/native/source/rail/world/corpus/HTTP/fuzzy/test-pin gates remain binding.
