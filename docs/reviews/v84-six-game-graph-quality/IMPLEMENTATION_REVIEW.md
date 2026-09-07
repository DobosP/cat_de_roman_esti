# V84 independent implementation review

Valid until: the reviewed runtime, help, transaction or historical-reconstruction code changes — then treat as history.

Reviewed 2026-09-07 by v84_graph_research. Scope: code authored by the other V84 agents, excluding my own tests/test_v84_graph_and_games.py implementation. No material actionable blocker found in the reviewed changes. This is a source and focused-test review, not browser completion, final integration approval or human playtesting.

## Earned Alchimie explanations

The response derives explanations from the existing server-owned two-parent lineage; it introduces no session fields, caches or retained histories. Seed items have no links. A result and each parent must already be in the visible inventory, and the actual selected graph edge must connect exactly that parent/result pair, have nonblank wording and not be a distractor. Thus an explanation can contain only two already-earned endpoints and cannot enumerate other neighbors or private recipe outputs.

Graph lookup selects the real strongest playable edge. Serialization preserves that edge's authored source, target and label, including reverse-authored bidirectional associations. It never turns an association into a fabricated ingredient recipe. The frontend renders these fields as escaped text in the reaction history and winning result, with an empty-links fallback for older response shapes. It makes no independent graph lookup or API request.

Independent focused execution: five explanation tests passed, covering bounds, hidden-node rejection, strongest edges, authored direction, reversed selection, free repeats, resume, reset and the winning result. No performance-wide conclusion is inferred from these small tests.

## Rules and keyboard behavior in all six games

GameHelp receives only the game key and static goal/feedback/recovery text. It has no state effects, event handlers, requests, local storage or access to a round's answer. All six active screens supply their own correct game key. The native details/summary element starts closed and provides keyboard behavior without a separate focus trap. Its summary has a 44-pixel minimum touch height and visible focus styling; long text wraps. Existing screen-level vertical scrolling remains responsible for expanded content.

The three existing global Enter handlers now ignore a focused summary: Alchimie cannot combine a ready pair, Conexiuni cannot submit four selected tiles, and a finished Lanț cannot start a new round while the player opens help. The change does not alter typing handlers or interfere with native Space activation. Existing Escape behavior is unchanged.

The text agrees with the current rule implementation: guesses/moves require their actual game semantics; repeated failed choices are free where promised; the helper itself consumes no clue or score. Alchimie and Perechi avoid equating associations with ingredient lists or synonyms. The source-level help tests and proposed desktop/mobile browser assertions cover these claims, but the final browser results were still pending at review time.

## Reviewed graph-edge removal

remove_reviewed_edges accepts only a sequence of full prior records. It rejects missing IDs, partial or stale records, duplicate requested removals, duplicate baseline IDs and JSON-type changes such as integer flags becoming booleans. Comparison is against the complete current record, not only endpoints or a guessed relation. Its filtering leaves the caller's original list unchanged.

The shared transaction validates the prospective graph after removals, includes removed endpoints in degree checks and preserves all original edge IDs during new allocation. A replacement cannot silently recycle the retired ID. The post-merge check verifies removed IDs remain absent. Existing approved-pack checks, mirrored files, both validators, mobile-contract refresh and full rollback remain in the same transaction. A failed stage restores and byte-verifies the original artifacts. Reapplying a stale removal fails rather than deleting anything else.

Independent focused execution: ten removal tests passed, including stale/partial/type rejection, corrected degrees, ID allocation, read-only dry run and restoration after an interrupted write. Together with explanation tests: **15 passed in 0.77 seconds**.

## Historical reconstruction

The V84 helper deep-copies its input, checks current metadata against the receipt and peels only exact added/changed/removed records. It rejects missing or duplicated IDs, checks replacement before/after rows, reinstates removed rows at reviewed positions and restores baseline order when recorded. It does not overwrite arbitrary live rows with expectations to make a test pass. Existing historical tests then retain their original baseline hashes.

I independently serialized all four inverse results and compared their entire bytes with Git baseline 8353880; all matched:

- KG: 4ce12d15ec247ebcaba3e119caed91f8d2624b09fa5568a8d7ece728f76a8a5e
- Pack: 78e680f3849f9a9de2a2675cbe7349ba23c8165f415cfc89a7533121bc34399c
- Rankings: f80397b3fc1dbfb58c9b4daf1e74fcebc43b698a5e290660333dad71a5d8dfb2
- Derived catalog: e406f182bbc8629b05dac9f2d58b51de45113f2917b8beeb078f8ddccf2a66af

A deliberately altered new Aluat label was rejected by the inverse. The removed synthetic Drojdie row is reinserted with its precise prior ID, anchor, penalty and order for old projection fingerprints. Final promotion must refresh the current receipt before final full validation; this review does not authorize stale bindings.
