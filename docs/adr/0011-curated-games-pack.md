# ADR-0011: Curated games pack — quality-first content with categories

Date: 2026-07-07
Status: accepted

## Decision

Add a curated content layer over the four word games: a bundled
`fixtures/games_pack.json` of hand/AI-authored game instances, each tagged with a
`category` (extended taxonomy: the 8 KG categories + a pop-culture shelf —
`muzica`, `film_tv`, `meme_net`, `sport`, `viata_de_roman`, `gastronomie`), a
`source` (`user` | `ai` | `ai_corpus`) and a review `status`
(`approved` | `pending` | `rejected`). Only `approved` items are served. All four
create endpoints accept an additive `?category=` param: curated instances are
served first; Contexto/Lanț/Alchimie fall back to category-scoped mining;
Conexiuni is curated-only per category (its boards cannot be mined single-theme
and gain authored `group_labels`). The shared daily prefers a curated instance
via rendezvous hashing once a game's pool reaches `CURATED_DAILY_MIN_POOL` (8).
User submissions enter via `POST /api/submissions` into a volume-backed pending
queue (`CAT_SUBMISSIONS_DIR`, off by default) and are promoted offline with
`scripts/review_submissions.py`. `scripts/validate_games_pack.py` is a CI gate
mirroring the KG-fixture validator idiom, sharing the exact validation functions
the server uses (`wordgames/packs.py`).

## Context / why

Boards mined directly from the KG at runtime are not good enough (owner call,
2026-07-07): mining optimizes for graph shape, not for the "aha"/shareability
that makes these formats viral. Pop-culture content — the intended growth engine
— does not exist in the KG at all, and three of the four games are structurally
KG-dependent (Contexto ranks by graph distance, Lanț walks edges, Alchimie
combines common neighbors), so pop culture arrives as an authored subgraph via
the existing densify pipeline, while curated instances pin the *good* boards on
top of it. Why not a DB: the server is deliberately stateless (ADR-era decision,
in-memory sessions, no migrations); a bundled, validated pack file keeps content
versioned in git and byte-reproducible, and the submissions queue is an
explicitly opt-in mounted volume rather than a persistence layer. Why
rendezvous hashing for dailies: pack growth must not reshuffle every historical
daily. Why a daily pool floor: a 1-item pool would serve the same "daily" every
day. `board_category` is echoed only when the player requested a category — a
curated daily stays themeless so Contexto's paid category clue and Conexiuni's
reveal gate keep their value.

## Consequences

Easier: shipping high-quality/pop-culture content is now a data change (pack +
fixture) behind two CI gates; user content has a safe intake path; the mobile
contract grows only additively (`meta_categories`, `submissions_create`,
optional `board_category`). Harder: the pack and the two fixture copies must
stay byte-identical and validator-green (CI enforces); mirrored game constants
in `packs.py` are drift-guarded by tests. The shared daily changes for a game
once its curated pool reaches the floor — an accepted, one-time discontinuity
per game (same precedent as the BFS determinism fix). Revisit when the
`romania_scraper` corpus is clean enough to auto-generate `ai_corpus` items, and
before real load arrives (submissions rate limit is in-memory, single-process).
