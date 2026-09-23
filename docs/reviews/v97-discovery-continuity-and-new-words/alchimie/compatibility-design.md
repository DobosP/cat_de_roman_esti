Valid until: the V97 compatibility decision is implemented and reviewed — then treat as history.

# V97 saved-book continuity proposal

**Recommendation for implementation review: explicitly increase the full-snapshot history bound from eight to sixteen, retain the 2 MiB catalog limit, and add the same byte check before a generator writes.** This is a proposal; no runtime, generator, fixture, test or limit has changed in this kickoff. Keep the reference-history codec as a measured alternative for a later format migration.

The immediate constraint is the version count, not the existing catalog size. V96 occupies **749,055 bytes**, including **363,050 bytes** when its eight full histories are serialized independently. Recording V96 as the ninth historical book would make the measurement-only catalog **815,543 bytes** before new content. Sixteen copies at V96's present history size project **1,280,959 bytes**, about 61% of the unchanged 2,097,152-byte cap. That projection is deliberately not an installable catalog: it repeats versions and includes the current fingerprint. Future books must be distinct, additive, independently reviewed artifacts; their actual size must be checked rather than assumed from this estimate.

The current runtime schema (`Catalog.compatible_versions`) and generator (`compatible_versions`) both enforce eight. The loader rejects a catalog above 2 MiB. The generator currently validates a parsed catalog but does not independently apply that file-byte guard before its atomic write. Any implementation of the proposed larger count must centralize the count constant, use it in both places, and reject an oversized candidate before touching the installed file. No increase to 256 concepts, 512 recipes, 96 supplies, twelve tiers, 256 saved crafts or the 64 KiB request bound is proposed.

Full snapshots preserve the strongest existing property with the least migration risk: a saved fingerprint selects its exact old recipes and supply thresholds. Restoration first checks every pair under those historical rules and only then replays earned discoveries into the current world. A new pair cannot be forged into an old save merely because today's world accepts it. Keep every old `world_id`, `recipe_hash`, `source_sha256`, canonical mechanics record and supply schedule. Never evict an oldest book to make room. Historical save support must remain verifiable against the exact reviewed archive rather than an arbitrary fingerprint allowlist.

The isolated prototype round-trips a smaller representation that stores each historical version's **explicit recipe IDs and unlock IDs**, resolving them against the current immutable recipe and unlock records. It recomputes canonical mechanics and checks the existing hash before accepting a reconstructed history. Nine histories shrink from **424,326 to 68,955 bytes** in that representation; the measurement-only full catalog shrinks from **815,543 to 429,210 bytes**. This saves substantial disk space, but needs a new strict history format, bounded lists, stable recipe/unlock identity enforcement, dual-format loader coverage and a trusted-archive conversion gate. It still needs an explicit version bound; deduplication does not justify unbounded histories.

The reference prototype reconstructs every old recipe and supply record exactly for eight historical books plus the current V96 book. It checks **1,009 earned prefixes** through the existing runtime, rejects **315 newer-pair forgeries** under older hashes, and rejects unknown/duplicate/missing recipe references, a changed hash/world and unknown supplies. It does not prove that an unimplemented schema migration is ready. Five warm current-world validations had a median around **10.7 ms** on this host; this is an observation, not a performance budget or benchmark guarantee.

Before implementation can install a ninth book:

1. Record the explicit chosen bound and retained limits in an ADR; add a named history constant rather than two new literals.
2. Keep all eight prior records exact and add V96 from its pinned reviewed candidate. Check actual serialized bytes before write; an over-limit write must leave the installed file untouched.
3. Exercise counts eight/nine/sixteen/seventeen, duplicate hashes, modified starters/supplies/recipes, unknown hashes, forged newer recipes, and every earned prefix from all nine books. Sixteen valid histories need a purpose-built additive fixture, not repeated size-projection entries.
4. Recheck live upgrades, empty-pair invalidation, restored saves and current hashes; public save shape and browser storage require no change for the full-snapshot option.
5. Run the normal two semantic reviews, live audit and two final reviews before any new words become served. Keep source and final review bindings exact.

Revisit reference encoding before a seventeenth book or when real serialized size approaches the existing byte budget. The two draft concepts are conditional on this compatibility work and separate factual/quality approval. They do not authorize a hidden cap change.

The first scratch generator-cap probe accidentally reused an existing starter pair and correctly hit the earlier changed-recipe guard. The corrected probe uses an unused pair and reaches the intended nine-history rejection. Both logs remain in this package.
