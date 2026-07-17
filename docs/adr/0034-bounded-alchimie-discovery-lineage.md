# ADR-0034: Show bounded Alchimie discovery lineage

Date: 2026-07-17
Status: accepted

## Decision

Render Alchimie's first-discovery lineage directly from the server-authored inventory.
Keep the newest reaction visible, group adjacent results that share the same unordered
parent pair, retain at most 12 reactions, and place older reactions behind a collapsed
disclosure. A result chip may only fill or clear a visible bench slot; the explicit
`Combină` control remains the sole submission path. Keep the server message as the one
nonterminal live announcement, suppress it at victory, and render the winning reaction
inside the result card. Accepted empty combinations use that same persistent status
instead of also emitting a toast.

## Context / why

The backend already records the exact submitted parent pair on first discovery and
serializes inventory in discovery order on create, get, combine, hint, and reset. The
browser previously exposed that lineage only through an HTML `title`, which is poorly
discoverable on touch. Little Alchemy's official
[encyclopedia guidance](https://help.littlealchemy2.com/encyclopedia/using-the-encyclopedia)
keeps discovered items and their relationships available and lets players deliberately
return an item to the workspace. Its
[changelog](https://help.littlealchemy2.com/changelog.html) documents input-aware
tutorials, easier item finding, and fixes for ambiguous touch activation. Experimental
game-feedback research links curiosity and legible action-to-result causality with
enjoyment, while excessive feedback can reduce agency
([CHI 2024 paper](https://people.csail.mit.edu/dkao/pdf/3613904.3642656.pdf)).
[WCAG status guidance](https://www.w3.org/WAI/WCAG22/Understanding/status-messages.html)
also warns against unnecessarily chatty live regions.

A permanently open 12-row history would dominate a 320 px screen; a latest-only local
card would lose older recovery and session restoration. Client-maintained recipes could
drift from server truth. Progressive disclosure over the existing inventory provides
memory without those costs.

## Consequences

Resume reconstructs the same bounded journal without new client persistence, and reset
removes it when the server returns seed-only inventory. Multi-result combinations remain
one reaction. Result actions have 44 px targets and never craft automatically. Recipe
validation, target-ID secrecy, scoring, hint rules, category scoping, two-hour sliding
TTL, and the 1,000-session cap are unchanged. Manual Romanian playtesting at 320–390 px
remains required when the in-app browser is available.
