# Independent portable Alchimie tooling review

Valid until: the bound implementation or dependencies change — then treat as history.

Accept the five-file source/documentation set recorded in `tooling-review.json`.
The extension supplies the evidence needed by the existing Alchimie applier without
changing that applier, the audit generator, the runtime or promotion policy.

Every Alchimie raw item requires the exact supplied audit byte hash from each reviewer.
Complete fresh dossiers, matching sorted Alchimie-only IDs and distinct role identities
are still mandatory. Private staging reproduces the archived sparse projection and
then checks live pack, graph, rubric, source records, runtime and generator bindings.
These checks finish before output copy. The original audit bytes and judgments survive
serialization; missing, mixed, stale or coherently restamped false evidence fails closed.

I independently checked the actual compressed test evidence and both decoded/archive
hashes: 44 tests initially, then one explicit unsorted-batch regression was added and
45 passed; the existing critique suite passed 102. The serializer bytes did not change
between focused runs. I did not duplicate these heavy checks or run full integration.

The tests exercise exact byte preservation, 21 negative evidence cases, preexisting
output preservation on rejection, distinct judges, mixed games, unsorted batches and
stale audit rejection. The guide and ADR match the implementation; ADR0104’s historical
body remains unchanged. No blocking issue found.

Limits: these are agent judgments, not human content acceptance. Reviewer IDs do not
cryptographically establish independence. As in the prior serializer, final publication
uses per-file atomic writes; an unexpected filesystem failure can leave partial output.
The unchanged applier still validates all artifacts before mutating any pack copy.
