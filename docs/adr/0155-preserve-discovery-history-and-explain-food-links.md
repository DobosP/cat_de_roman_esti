# ADR-0155: Preserve discovery history and explain food links

- Status: accepted
- Date: 2026-09-17
- Extends [ADR-0154](0154-expand-content-and-clarify-input-recovery.md).
- Partially supersedes [ADR-0146](0146-expand-alchimie-and-preserve-collections.md)
  and [ADR-0147](0147-grow-alchimie-with-reviewed-vocabulary.md) for the historical-book limit only.

## Decision

Complete V97 through independent factual, quality, allocated and final runtime reviews,
then land it under the owner's instruction and begin V98 from landed main. Add one
Conexiuni board, one Cald sau Rece target, one Lanț round, two quick boards and two
Alchimie preparations with two recipes each. Preserve earlier records and pending holds.

The eight historical Alchimie books are full. Increase the single shared historical-book
limit to sixteen, preserving all existing histories and adding the exact V96 book.
Do not evict a history to make room. Keep full recipe and starter validation, distinct
version hashes, chronological craft validation, and rejection of forged newer pairs.
Keep the catalog at 2 MiB and check serialized bytes before any candidate, proposal or
installed output write. The next history beyond sixteen fails closed. This is finite
headroom, not a permanent migration strategy.

All other bounds remain: 256 concepts, 512 recipes, 256 saved craft pairs, at most twelve
starters, 32 goals, 64 KiB requests and the existing session limits. The authored inventory
retains its eight starters, 96 supplies, twelve tiers and 32 goals exactly.
V97 uses 251 concepts and 351 recipes; future content work must respect the remaining
five concept slots or separately review a capacity decision.

Install twelve food relationship captions for three earlier Lanț rounds. Each noun
phrase binds the full existing edge snapshot and passes two distinct reviewer roles.
Preserve all 101 earlier captions. The registry explains an already displayed choice,
earned hint or completed step; it does not reveal a future route. A changed edge loses
the reviewed caption. Fourteen existing directions receive the text; ten nonexistent
reverse directions remain unavailable. Recipe variants are described without claiming
that optional sugar, vanilla or a particular cake construction is universal.

## Consequences and verification

The extra save history permits additive content without discarding earned progress.
The 2 MiB guard bounds its storage cost. Both new vegetable dishes remain terminal;
V98 should evaluate onward uses and vocabulary gaps alongside new concepts.

Backend checks cover the ninth and sixteenth history, rejection of a seventeenth,
byte-boundary writes, historical replays and caption direction/fallback behavior.
Real desktop and narrow mobile browser journeys check visible choices, keyboard use,
completed paths and reload. The new Cacao→Lapte round still has generic captions;
its associations are independently reviewed and its wording remains future work.

Exact results and review provenance live in the [V97 review](../reviews/v97-discovery-continuity-and-new-words/README.md)
and [STATUS](../STATUS.md). Automated checks do not establish human enjoyment.

## Browser integration correction (2026-09-22)

Resumption testing found that the browser still rejected more than eight compatible
recipe hashes, even though this decision expands the server bound to sixteen. The
ninth valid book made a freshly saved collection unreadable on its next update. Match
the browser validation bound to sixteen, preserve all existing hash and save-size checks,
and exercise nine/sixteen-book owned updates plus rejection of a seventeenth. The actual
bundled catalog is included in the browser save regression so this limit cannot silently
drift again.

A separate replay check reproduced a persistent error moving above the viewport when
the temporary notification row disappeared. Reveal the full error paragraph once when
failure becomes visible, inside its existing scroll container, without moving keyboard
focus. Later manual scrolling remains the player's choice. Re-check complete clipping
before/after notification expiry and unchanged focus across the held failed response.
The original failed integration remains evidence; the final assembled gate record must
cover these fixes before V97 is described as verified.
