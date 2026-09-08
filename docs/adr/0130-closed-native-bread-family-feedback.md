# ADR-0130: Restore a bounded native bread-family cue

- Status: accepted
- Date: 2026-09-08

## Context

V87 gave Brioșă its correct native identity and retired its broad Pâine projection.
That cooled false affinities elsewhere but made Brioșă→Pâine rank424/cold. The native
term deliberately covers both brioche and modern muffin-like Romanian usage.

## Decision

Add one closed native exact-target feedback pair: Brioșă for hidden Pâine. Use the
existing related-word rank2 mechanism without changing its formula. Keep the submitted
native identity, require the exact target for a win, and leave every other target's
native Brioșă behavior intact. Do not restore its old projection or add an unconditional
is-a edge or synonym. Projected inputs cannot inherit the native exception.

The dictionary's cozonac-style sense and a producer's actual brioche bread variants
support family relevance. Modern Romanian muffin usage limits the claim. The rank is
an explicitly generous editorial interpretation, not a fact asserted by those sources.
Independent review accepted this exact scope with that qualification. Brioșă/Pandișpan
hidden targets remain deferred, and no Chec→Pâine exception is added.

## Acceptance and limits

Check all existing forms, nonwinning identity, repeat handling, exact answers, public
answer privacy, typo filtering and all-target policy isolation. Compare old approved
Contexto observations on unchanged graph bytes before mixing in V88 topology changes.
Keep session/request bounds and all prior graph/projection/policy records unchanged.
The scoped source and independent review are in
`docs/reviews/v88-cross-game-quality/bread-feedback/`; full V88 integration is separate.
