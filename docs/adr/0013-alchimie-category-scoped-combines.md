# ADR-0013: Alchimie combines are category-scoped

Date: 2026-07-07
Status: superseded-by ADR-0044

## Decision

Every Alchimie game is themed to a single category, and a combine of two concepts
yields their common neighbours **restricted to that category's subgraph**
(`WordGameService.common_neighbors(a, b, category=…)`). The category is the curated
item's own category, the player-requested `?category=`, or — for an un-themed mined
game — one picked deterministically at build time. The combine-closure, opening-pair
count, seed growth, the runtime combine endpoint, the nudge, and the pack validator all
scope to the game's category. `AlchimieSession.category` is therefore always set and
always echoed (`board_category`).

## Context / why

The alias + play-density batches (v6–v9) took the graph to ~1,300 nodes / ~5,400 edges,
mean degree ~8 — great for Cald sau Rece and Lanțul (findable paths) but **fatal for
Alchimie**: the unscoped combine-closure reached ~the whole graph (1,299 of 1,304 nodes
from 6 seeds). Consequences: every target became craftable in ~2 generations (the game
lost its "deliberate steps" structure), and each closure took ~1–2s so validation and
mined-game creation were slow (a 140-item batch timed out; v9 had to drop it). Strength-
gating the combines was measured and rejected — the graph is densely connected with
*strong* edges (median strength 0.78; 88% ≥ 0.6), so a threshold barely shrinks the
closure. Category-scoping does: measured closure drops to ~84–106 nodes in ~0.005s, with
targets spread across generations 1–5 — exactly the bounded, structured space Alchimie
needs. Why it's safe to always expose the theme (unlike Contexto/Conexiuni, whose
category is a hidden/paid reveal): Alchimie already shows the target's label and
description as the goal, so the theme is not a secret.

## Consequences

Alchimie regains structure and is fast again (combine/create/validate all ~instant);
mined games are always themed (a one-time change to which instances a seed produces —
accepted, like prior daily discontinuities). Pack re-derivation under scoping dropped 4
of 15 legacy Alchimie whose targets are not craftable in-theme; the rest are valid.
Growing the Alchimie pool now uses a category-scoped generation round. Revisit if a
cross-category Alchimie mode is ever wanted (would need an explicit multi-category scope,
not the whole graph). The closure math lives in two mirrored places (`wordgames/alchimie.py`
runtime and `wordgames/packs.py` validation) — both take the `category` arg; keep them in
lockstep.
