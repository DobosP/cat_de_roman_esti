# ADR-0037: Extend beginner vocabulary with concrete everyday concepts

Date: 2026-07-17
Status: accepted

## Decision
Keep the completed v24 benchmark as its historical 234/234 contract and add a separate
17-term beginner extension as first-class easy concepts. Give the extension 66
collision-screened inflections and 64 explicit directed semantic edges. Every new node
must have at least four distinct playable neighbors, two same-category neighbors, two
forward choices, and one incoming cue; no existing endpoint may gain more than three
new neighbors. Add no curated board or promotion.

## Context / why
Words such as `câine`, `cămașă`, `minut`, `coleg`, and `trotuar` are concrete and useful
to beginners, but none had an honest resolver owner. Mapping them onto nearby composite
titles, idioms, objects, or people would create false aliases; generic `related_to`
links would make routes feel arbitrary. The separate extension makes growth visible
without rewriting the denominator of the already completed benchmark. Bare `somn`,
`duș`, `pod`, `burtă`, and `braț` remain deferred because ordinary homonymy or accent
folding cannot select one safe sense.

## Consequences
The fixture becomes 2,216 nodes, 8,909 edges, 7,143 aliases, and 180 legacy puzzles;
the extension resolves 17/17 and combined eligible probes resolve 251/251. Deterministic
regeneration changes 30 legacy puzzle records. Both critique reports remain
byte-identical: the exact 33-item set is clean and the full 222-pending inventory gains
no finding. The 794-record curated pack stays byte-identical and unpromoted. The public
mobile contract must move to `fixture-v29-extended-basic-words`; session TTL and caps do
not change.
