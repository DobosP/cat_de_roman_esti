# Native content rails

The private `cat-content-rail` executable ports the quick supplement, exploration
world, bounded recipe extension and finite V1 reserve builders/audits. Authored
inputs and the extraction receipt are described in [sources](sources/README.md).
Current reviewed fixtures and their pins remain unchanged.

```sh
# Recompute all four baseline artifacts and require exact approved bytes.
cat-content-rail all --root ROOT --check

# Generate a new source/version-bound candidate (quick, world or extensions).
cat-content-rail quick --root ROOT --source SOURCE.json --candidate-out CANDIDATE.json

# Construct a proposal from complete independent semantic judgments.
cat-content-rail quick --root ROOT --source SOURCE.json --candidate CANDIDATE.json \
  --factual-review FACTS.json --quality-review QUALITY.json --proposal PROPOSAL.json

# Offline native selection/gameplay or world/core/history audit.
cat-content-rail quick --root ROOT --audit-catalog PROPOSAL.json --audit-out AUDIT.json

# Install only after the exact saved proposal/audit and both final judgments.
cat-content-rail quick --root ROOT --source SOURCE.json --candidate CANDIDATE.json \
  --factual-review FACTS.json --quality-review QUALITY.json --proposal PROPOSAL.json \
  --live-audit AUDIT.json --final-factual-review FINAL-FACTS.json \
  --final-quality-review FINAL-QUALITY.json --expected-sha256 REVIEWED_SHA --write
```

`world` and `extensions` use their retained review kinds. `reserve --check`
reconstructs the finite 20-pack/3-quick manifest from immutable independently
reviewed proposals. Its optional `--write --expected-sha256` requires the exact
existing reviewed manifest pin and updates both copies through the shared locked
transaction. Candidate/proposal/audit output cannot replace source or fixture
inputs or follow a symlinked output parent.

The quick audit exercises all accepted supplement boards through ordinary seeded
HTTP creation, scored play and terminal resume in a private in-process server.
The world audit verifies all 33 goal modes, all 351 recipes, nine historical books
and all 1009 saved prefixes. Recipe audits verify every unchanged core, route,
par and node/edge snapshot for the approved additions. No solution/debug endpoint
is installed, and no provider, live data import or production activation occurs.
