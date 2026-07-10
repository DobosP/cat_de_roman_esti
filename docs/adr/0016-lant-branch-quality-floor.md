# ADR-0016: Lanț requires real shortest-path choices

Date: 2026-07-10
Status: accepted

## Decision

Serve a curated Lanț board only when at least two legal first moves lie on a shortest
path and every intermediate shortest-path layer contains at least two nodes. Calculate
the path diamond with forward distances from the start and reverse-BFS distances to the
target, preserving directed edge semantics. Use this one shared branch profile in the
miner and curated-pack validator. Keep boards that fail the floor as pending review,
never in runtime pools.

## Context / why

The miner already described this floor as the difference between a satisfying word
ladder and a forced rail, but the curated validator checked only reachability, distance,
and difficulty. As a result, 98 of 187 approved boards funnelled the player through a
single opening or intermediate node. The old audit also used
`distances_from(target)`, which answers the wrong question for the fixture's 107 directed
edges; two false positives and two missed failures happened to leave the same total.
Adding broad shortcut edges merely to rescue authored pairs was rejected because it
would distort every other graph game. The weak boards remain reviewable rather than
being deleted.

## Consequences

Lanț has 89 approved and 106 pending boards; every category retains at least three
approved choices, and each difficulty retains at least nine. Ordinary and daily picks
may change once because the reviewed pool changed, while the bounded branch-aware miner
remains fallback for thin filters. New submissions and imported approved content must
clear the same floor. The reverse-distance primitive also makes directed hints and
same-label disambiguation cheaper and correct. Session TTL and capacity remain six hours
and 10,000 entries per game.
