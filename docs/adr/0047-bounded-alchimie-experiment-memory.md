# ADR-0047: Remember bounded Alchimie experiments server-side

Date: 2026-07-19
Status: accepted

## Decision

Keep one server-authoritative set of canonical unordered attempted pairs in each
Alchimie session. Charge and resolve only the first submission of a distinct owned
pair. Return a repeated barren or formerly productive pair with authoritative state,
`already_tried = true`, no discovery, and no mutation to moves, score, fruitless
streak, hint state, or inventory. Return `already_tried = false` for every first
submission. Reset clears the set. Public state exposes only `attempted_count`; neither
the set, ingredient IDs, results, nor private routes are serialized.

Derive the hard memory ceiling from the existing 32-concept projection:
`C(32, 2) = 496` unordered pairs. Reject a new pair after that ceiling defensively;
valid projected sessions cannot produce such a request. Preserve the correction bench
from ADR-0035, but let the server verdict cover pairs reconstructed after another
selection, a resume, or another client. Keep the two-hour sliding session TTL and
1,000-session LRU cap unchanged.

## Context / why

ADR-0035 blocked only the immediately retained empty pair in one browser. Rebuilding
that pair after an edit or on another client spent another move, and a pair that had
previously produced a concept later looked barren once its result was already owned.
Those retries rewarded remembering client state rather than exploring the word space;
they could also inflate the fruitless counter and unlock hints without new experiments.

A client-only history would drift across resume and duplicate authority. An unbounded
server log or a log of results would consume unnecessary memory and expose route clues.
The projected inventory already supplies a small mathematical bound, while a set gives
constant-time membership and needs no eviction policy inside a live game.

## Consequences

Players can safely reconstruct an old experiment and receive a short correction without
losing a move. Every move and every step toward a hint now represents a distinct pair.
The UI may search the complete discovered inventory while a compact, accent-insensitive
query is active, and it keeps the ready-pair marker explained visibly without exposing
partner IDs. Resume preserves experiment memory; reset deliberately starts it over.

Session state grows by at most 496 two-ID keys and public payloads gain one count; combine
payloads gain one boolean verdict for the submitted pair. Target-ID secrecy, sparse
recipes, exact par, scoring, deterministic construction, category scoping, session TTL,
and session-store cap are unchanged. This ADR supersedes ADR-0035's rejection of
persistent tried-pair memory while retaining its correction-bench interaction.
