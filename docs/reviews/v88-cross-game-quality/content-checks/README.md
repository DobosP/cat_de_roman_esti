# V88 content integration checks

Valid until: source/artifact hashes change — then retain as history.

The final new suite passed **59 tests in 6.67 s**. This includes exact baseline reconstruction
of all four content artifacts, tamper rejection, every new typed form, all 33 directed moves,
correct sour/sweet/whipped cream identities and three genuinely public selectable round journeys.

The focused integration attempt covered 285 tests:282 passed and3 new inverse assertions failed
because they used two-space KG JSON formatting for the one-space pack/rankings/derived files.
The assertion formatting was corrected and all 59 new tests passed afterward. All 226 other
historical/generic cases passed in the focused attempt. Root full integration remains separate.

An earlier 50-case run also exposed 26 incorrect test assumptions about Lanț's compact invalid-move
response, plus 1 projection check executed before retirement was applied. Those tests now inspect
authoritative GET state. The corrected 49 applicable cases and 2 projection/audit cases passed.
Exact unaltered logs are archived losslessly; [verification.json](verification.json) records
both decoded and gzip hashes, actual outcomes, source/artifact bindings and command scopes.

[current-pins.json](current-pins.json) records the manually reviewed current expectations:
2,413 concepts / 9,442 links / 8,631 forms / 180 puzzles, 658 pack records / 650 approved / 8 pending,
488 eligible rounds and 465 projected terms. Frozen 336 derived rows are unchanged. Pin updates
change 35 literal values in the existing snapshot; live and historical expectations remain separate.

The V86 source and review stay immutable. Its former fermented-cream→Frișcă link is replayed
only against reconstructed history; the V88 suite requires its current rejection and the qualified
sweet-cream replacement. The V87 inverse assertions similarly peel V88 before checking history.
No new Contexto hidden target or human playtesting is claimed.

## Full-matrix historical guard corrections

The initial full backend runs exposed seven additional assertions outside the focused subset.
[The remediation receipt](diagnostic-remediation.json) preserves the actual seven-failure
tracebacks, one node collection, positional mapping and seven green follow-up results
(**7 passed in 36.41 s**). No runtime or content changed in this correction.

The original 79-board sparse digest and median 0.66 are verified against reconstructed V87.
All current sparse bounds remain in force for 80 approved boards; its measured median is 0.67.
Current inventory/high-water uses the shared snapshot; historical V48's 99-record inventory
is reconstructed separately from the newly added V88 board.

The original V31/V44 sink isolation also remains exact on reconstructed V87. ADR-0131
records the reviewed Făraș→Mătură→Podea opening: exactly six cleaning nodes now reach the
mature graph, all other former sinks remain isolated, and all 71 feedback mappings remain
byte-exact. Removing only the Făraș→Mătură bridge in memory restores the old isolation.
This explicitly tests the changed decision rather than dropping a failed requirement.
