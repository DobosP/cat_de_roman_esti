# ADR-0022: Confident typo auto-accept + smarter Lanț guidance

Date: 2026-07-13
Status: accepted; decision 2 superseded-by ADR-0043

## Decision
Make near-miss input playable instead of merely advisable, and make Lanț's guidance
honest about branches and dead ends. All response changes are additive; operationIds,
`score_for`, clue rules (ADR-0005), directed distances (ADR-0018) and the hidden-answer
boundary (ADR-0009) are unchanged.

1. **Confident auto-accept.** New `WordGameService.resolve_fuzzy(text)`: when exact
   `resolve()` misses, score every normalized index key (labels, ids, aliases) with
   `difflib.SequenceMatcher.ratio` and keep each node's best ratio. Return the top node
   only when it is high-confidence (ratio >= 0.90) AND unambiguous (no second distinct
   node within 0.06 of it); ties read as ambiguity. Deterministic. Contexto's guess and
   Lanț's move play the corrected node exactly as if typed — attempts/moves count
   normally — and say so via an additive `message` ("Am înțeles: <label>."). A rejected
   Lanț correction names the corrected label in the standard error ("Am înțeles: X.
   Nu exista o legatura directa"). **A confidently corrected typo of the answer is a
   legitimate WIN** in both games: the player knew the answer; a phone typo must not rob
   it. Anything below the bar keeps ADR-0021's advisory `suggestions` (Contexto still
   strips the target there, ADR-0009).
2. **Lanț hint = strongest hop, then visible branchiness.** Among shortest-path
   neighbours the hint now orders by (edge strength of the current->candidate hop DESC,
   salience DESC, id) — the tight semantic link is the association a player can actually
   follow; fame only breaks ties. The session counts hint requests per exact chain
   state; from the SECOND request at the same position the payload adds
   `alternatives_labels` (up to 3 other on-path labels) and a message ("Alte variante:
   A, B."), making the ADR-0016 branch floor visible to a stuck player.
3. **Dead-end early warning.** A legal Lanț move onto a node whose directed
   `distances_to(target)` is unreachable adds `dead_end: true` and appends a short
   warning to the move message — the entry-side pair of ADR-0021's backtrack hint.

## Context / why
ADR-0021 made typos *visible* ("Poate cautai: X?") but still cost a round-trip: on
phones nearly every guess with a missing diacritic or dropped letter stalled the game,
and a typo'd correct ANSWER read as an unknown concept. The 0.90/0.06 thresholds were
chosen so a single dropped/added character in a >= 6-char label auto-accepts, while
genuinely ambiguous inputs (two nodes one character apart, e.g. singular/plural label
pairs) and heavier mangling stay advisory. Auto-accepting the target cannot leak it on a
non-win by construction — correction == target implies distance 0, which IS the win —
so the ADR-0009 surface is untouched. In Lanț, the salience-first hint often nominated a
famous but weakly linked hop that players did not associate with the current concept,
and the guaranteed branchiness (ADR-0016) was invisible exactly when someone was stuck;
repeating a hint request from the same position is the cleanest "still stuck" signal we
already have. The dead-end flag moves ADR-0021's escape hatch from the hint (pull) to
the moment the mistake happens (push), while still naming only nodes the player typed.

## Consequences
Unresolved-input tests that relied on one-char typos staying advisory are updated to
heavier typos (deliberate); the Lanț hint-preference test now pins strength-first
ordering. `resolve_fuzzy` is O(index) per miss with difflib's quick-ratio pruning —
negligible at current graph size. Lanț sessions carry a per-position hint counter
(bounded by positions visited); every successful non-winning move now runs one extra
O(V+E) BFS for the dead-end check, matching what a single hint request already cost.
Frontends need no change (fields are additive), but can render `message`, `dead_end`,
and `alternatives_labels` for a better mobile feel.
