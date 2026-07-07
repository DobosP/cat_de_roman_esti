# ADR-0012: Exact alias layer + play-density enrichment for Contexto/Lanț

Date: 2026-07-07
Status: accepted

## Decision

Give every KG node an optional `aliases` list — alternate EXACT surface forms
(inflected/articulated forms, strict synonyms, common short titles, abbreviations)
that the text resolver accepts for the same concept. Labels always win over
aliases; the fixture validator enforces one meaning per typed word
(`alias_unique`) and short, typeable labels (`label_style`: concept labels and
ALL aliases ≤ 5 words; proper titles of works/orgs/events are exempt but carry
short aliases). Alongside aliases, run play-focused densification batches:
guess-vocabulary hub concepts (1–3-word labels) and intuitive edges that lift
low-degree nodes to degree ≥ 3, imported via `scripts/import_enrichment.py`
(alias hygiene, duplicate-concept remap, fixture merge + full games-pack
re-derivation, double validator gate).

## Context / why

Cald sau Rece and Lanțul Cuvintelor were data-starved (owner report,
2026-07-07): with ~695 nodes / 1,852 edges, 170 nodes sat at non-distractor
degree ≤ 2, so ladders dead-ended and natural guesses read "Nu cunosc acest
concept" or "Înghețat". Two distinct causes, two fixes: *coverage* (players type
"sarmalele"/"automobil" and the graph only knew "Sarmale"/"Mașină") is solved by
aliases; *connectivity* (no findable paths) by targeted densification. Why exact
aliases and not fuzzy matching/embeddings: the owner wants exact-word gameplay —
a typed word either denotes a concept or it doesn't; fuzzy matching would blur
scoring, hidden-answer guarantees, and determinism. Why the ≤5-word cap: labels
are things a player must TYPE mid-game; sentence-like labels are unplayable.
Aliases must be same-referent only (an association like "mămăligă"→"mălai" is an
edge, not an alias) — the generation verifier blocks wrong-referent aliases and
the importer drops collisions mechanically.

## Consequences

Easier: guess coverage grows without inflating the concept space; long official
titles stay factually correct while being typeable via short aliases; future
content batches carry aliases natively (densify merges them). Harder: every
graph merge now re-derives all pack numbers (`rederive_existing_items` — new
edges shorten distances); alias data must stay collision-free (validator-gated).
The fixture content-hash changes with any alias edit — expected manifest
behavior. Revisit if the graph outgrows the in-memory resolver index (fine for
thousands of nodes) or when the `ai_corpus` pipeline starts emitting aliases
from real corpus variants.
