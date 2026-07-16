# ADR-0032: Build game-specific beginner vocabulary from a reproducible common-word gate

Date: 2026-07-17
Status: accepted

## Decision

Persist a 236-surface Romanian beginner benchmark and require at least 90% exact,
semantically intended resolution after excluding explicitly recorded homonym collisions.
Add everyday concepts through a deterministic source and rollback-safe builder. Every new
node must have at least four meaningful incident links and two same-category neighbours;
at least 80% of the independently listed intuitive pairs must be direct. Stage a bounded
pending wave for every word game, with no runtime exposure before ADR-0023's bound analyst
and adversarial-verifier review.

Apply different content gates to the four loops. Cald sau Rece keeps a broad guess surface
but familiar targets, with at least 120 inbound-reachable nodes, at least 40 nodes within
five hops, and human-legible nearer-than ordering probes. Lanț keeps 2–3 / 3–4 / 4–6 hop
bands, requires at least two shortest-path first choices and two nodes in every intermediate
layer, and prefers three of each for beginner boards. Alchimie keeps five to seven seeds,
an exact two-to-six-action solution, a 15–60 concept closure, and a deliberately sparse
opening in which roughly 15–30% or more of seed pairs are productive without generic-hub
explosions. Conexiuni keeps one checkable 4×4 partition, familiar tiles, type-coherent
groups, and at most a controlled red herring. Any change to an existing approved record,
or any fixture/pack mirror or validator failure, aborts and restores all four files.

## Context / why

The pre-wave audit resolved only 94 of 236 ordinary probes (39.8%). `morcov` was absent,
while `mâncare` resolved but had none of thirteen obvious food neighbours, so global graph
reachability hid a frustrating local vocabulary gap. A separate 168-word check found only
28.6% semantically correct resolution and exposed harmful wrong-sense matches such as
`barcă` to FC Barcelona. Degree-only densification cannot distinguish that experience.

The balance follows the useful constraints of the English reference games rather than
copying their language or scale. [Semantle](https://semantle.com/faq/) accepts unlimited
single-word guesses while drawing secrets from a familiar 5,000-word pool;
[NYT Connections](https://thenewyorktimeshelpcenter.helpjuice.com/360011158491-New-York-Times-Games/28525912587924-Connections)
uses sixteen tiles and one four-group solution; [Wikispeedia](https://dlab.epfl.ch/wikispeedia/play/)
guarantees a route through a bounded article set; and
[Infinite Craft](https://neal.fun/infinite-craft/) makes combinations immediately legible
from four familiar starting elements. The Romanian vocabulary inventory is grounded in the
[CoRoLa frequency lists](https://zenodo.org/records/7091535), then filtered for concrete,
beginner-playable concepts rather than accepting corpus rank alone.

Why not add every colliding surface now: the resolver has one accent-folded ID per spelling,
so bare homonyms would silently choose a wrong sense. Record those terms as deferred until
the resolver can represent sense buckets. Why not approve generated boards directly:
mechanical solvability does not establish predicate honesty, route meaning, or recipe
intuition. Why not connect every word to one hub: that improves aggregate degree while
making Lanț trivial and Alchimie noisy.

## Consequences

The benchmark, graph inventory, semantic pair list, and application procedure are now
tracked and reproducible. The landed wave adds 150 nodes, 511 edges, and 276 aliases;
218 of 234 eligible benchmark surfaces now resolve to their intended sense (93.2%). It
stages 26 pending items—four Conexiuni, eight Cald sau Rece, eight Lanț, and six
Alchimie—while preserving all 572 approved records byte-for-byte. Exact deterministic
critique reports no finding for those 26 items or the seven v23 items rechecked against the
new graph. The richer graph improves typed guesses and direct beginner associations without
changing session TTL, size caps, hidden answers, scoring, or selection rules.

The single-sense resolver remains a known limit. Deferred collisions need a later ADR and
interaction design before they may enter the exact-resolution denominator. Future content
waves must rerun this benchmark and the per-game quality tests, not claim coverage from raw
node or edge totals. The staged items remain invisible until the subjective analyst and
adversarial-verifier gate judges predicate honesty, route meaning, ordering, and recipes.
