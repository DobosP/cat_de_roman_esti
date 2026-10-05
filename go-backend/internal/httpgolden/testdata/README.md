# Independently captured HTTP references

`python-http-parity.json.gz` captures all 1207 established anonymous HTTP cases
from the Django application using `scripts/check_go_parity.py` at base
`ae70c16935d402719b95405685bccbbbea13a3bd`. Expected statuses and bodies were
captured from the independent Django client, while the existing comparison
simultaneously verified the baseline Go server. The capture changes only random
session identifiers to stable aliases. It includes malformed bodies and queries,
Unicode validation, source rotation, curated/mined/daily selection, complete
scored journeys for all six games, and exploration validation/restoration routes.

Compressed SHA-256:
`9041e05f13190a06a526c1aeed1f264d467483cd267ffcdb24f422ed9430b2cb`.
`Frozen()` preserves this historical corpus, digest, 1207 cases and original eight
source identities. Replay requires exact equality with the selected export's source
digests. It refuses stale content references before
sending requests. It does not accept generated candidate output as independent
expected parity. The generic capture command requires an explicit reference name
and marks reference independence unverified.

A changed content source requires independently reviewed reference capture; do
not rewrite this corpus from the candidate merely to make a failing gate pass.

`python-http-parity-v1-2.json.gz` contains a separate independent Django capture
for the V1.2 reviewed graph and regenerated source catalogs. Its compressed
SHA-256 is `6293a0dde67ee0b0e5929cc1103bd80795e0aff1af2ba5fdf53e983ab79351fd`
(33,601 bytes; 1207 cases). The retained original capture author was adapted only
for repository/output paths and the reference label; request logic is unchanged.
Only random session IDs are normalized. All 1207 expectations matched the current
Go server during capture. Provenance and independently executed comparison:
[capture verification](../../../../docs/reviews/v1-2-content-growth/reference/capture-verification.json).

`ForSources` selects between the two digest-verified corpora using exact equality
of all source identities. Default parity selects before opening its transport;
unknown, missing, extra or mixed source sets refuse. `Replay` retains its separate
source equality and exact response checks. New content needs a new independently
captured reference; neither fixture rehashing nor native self-capture adds one.
