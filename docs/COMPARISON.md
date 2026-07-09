# cat_de_roman_esti vs. existing word games — quantity & quality

_As of v11 (2026-07-07). Positions the game against the formats it borrows from._

## The one-paragraph read

Every game below is a **single format** over a **single content source**. `cat_de_roman_esti`
is the only one that runs **four puzzle formats over one curated Romanian cultural knowledge
graph** — and it is the only Romanian game doing NYT-Connections / Contexto / word-ladder /
Infinite-Craft styles at all. It trades "effectively infinite but uncurated" content for a
**fact-checked, difficulty-calibrated, quality-gated** corpus. So on raw *quantity per format*
it is smaller than embedding- or LLM-backed games; on *quality per puzzle* and *breadth of
format + cultural specificity* it is ahead of every comparator.

## Quantity

| Game | Formats | Content scale | Source | Curation |
|------|---------|---------------|--------|----------|
| **cat_de_roman_esti** | **4** (Conexiuni, Cald sau Rece, Lanțul, Alchimie) | **619 approved curated games** (168 / 235 / 168 / 48) + 196 pending; **1,294 nodes / 5,370 edges / 4,538 aliases**; 14 categories | Curated Romanian KG | Dual-verified (factual + game-quality), every item |
| NYT Connections | 1 (grouping) | ~1,116 puzzles (1/day since Jun 2023) | Human editors | Gold-standard, hand-authored |
| Contexto | 1 (semantic hot/cold) | 1 word/day; ranks over the **whole language** via word embeddings | ML embeddings | None per-puzzle (model-driven) |
| Infinite Craft | 1 (combine) | "Infinite" — LLM generates elements on the fly (millions of recipes) | Llama LLM, live | **None** — accepts hallucinations |
| Wordle RO | 1 (letter guess) | 1 five-letter RO word/day | Word list | Simple dictionary |

**What 619 curated games means in practice:** across 4 games × 14 categories with difficulty
tiers and a daily, that is **months of fresh daily content** without repeating a board — plus
the mined fallback for the three graph-derived games extends it further. It is not "infinite,"
by deliberate choice: uncurated infinity (Infinite Craft) ships nonsense, and per-puzzle-only
games (Contexto/Wordle) give you exactly one puzzle a day.

## Quality

| Dimension | cat_de_roman_esti | Best comparator | Where cat stands |
|-----------|-------------------|-----------------|------------------|
| Factual correctness | Every node/edge/board fact-verified; wrong-referent + false-attribution blocks dropped | NYT (human editors) | **On par** with the gold standard, at a fraction of the human cost |
| Difficulty calibration | Salience recalibrated to balanced tiers (easy 441 / med 517 / hard 336); per-game difficulty selection (Lanț endpoint-salience by tier, Contexto salience pools, Conexiuni entanglement) | NYT (purple = hardest) | **Ahead** — explicit, data-driven, 3 tiers × 4 games |
| Answer integrity | Server-authoritative, hidden answers, reveal-gated (no client-side leak) | NYT / Contexto | **On par / ahead** (formal invariants + tests) |
| Input forgiveness | 4,538 exact aliases (inflections/synonyms/short titles) so natural typing resolves | Contexto (embeddings tolerate anything) | Behind embeddings on raw recall, but **exact + predictable** (no arbitrary "close" rankings) |
| Cultural specificity | Romanian history/literature/geography + 6 **pop-culture** shelves (manele, Las Fierbinți, meme, sport, viața de bloc, gastronomie) | none | **Unique** — no comparator is Romanian-cultural |
| Content coherence | Bounded curated KG — every combine/link is a real, human-sensible relation | Infinite Craft (LLM = often absurd) | **Ahead** on sense; behind on novelty/surprise |

## Honest weaknesses (and why they're acceptable)

- **Smaller vocabulary than Contexto.** Contexto ranks the *entire language* via embeddings; cat
  guesses against a ~1,300-node KG. Mitigated by the alias layer + a core-vocabulary pass so the
  words a player types first resolve — but a rare word Contexto knows, cat may not. Trade: cat's
  distances are *sharp and explainable* (real graph hops), not a black-box similarity score.
- **Not infinite like Infinite Craft.** By design — infinity there means uncurated LLM output.
  cat's Alchimie is category-scoped and quality-judged, so every craft makes sense.
- **No network/multiplayer yet.** NYT's moat is social + habit. cat has a daily + shareable
  results but not yet a leaderboard network.
- **48 approved Alchimie is the thinnest pool.** Recently fixed (category-scoped combines, v10);
  growable on demand.

## Where cat_de_roman_esti wins

1. **Format breadth** — 4 games in one app; every comparator is one format.
2. **Curated + verified quality** at scale without per-puzzle human authoring — a repeatable
   AI-generate → dual-verify → quality-gate pipeline.
3. **Romanian cultural identity + pop-culture virality** — a category no global game serves.
4. **Difficulty you can trust** — explicit, measured tiers, not a single "today's puzzle."

Sources: [NYT Connections archive](https://connectionsplus.io/nyt-archive) ·
[Contexto (embeddings, daily)](https://contexto.uk/) ·
[Infinite Craft (Neal.fun, LLM)](https://en.wikipedia.org/wiki/Infinite_Craft) ·
[Wordle RO](https://wordlero.vercel.app/)
