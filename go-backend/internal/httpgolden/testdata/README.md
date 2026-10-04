# Frozen independent HTTP reference

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
The replay checks the digest, exactly 1207 cases and exact equality with all eight
current reviewed source digests. It refuses stale content references before
sending requests. It does not accept generated candidate output as independent
expected parity. The generic capture command requires an explicit reference name
and marks reference independence unverified.

A changed content source requires independently reviewed reference capture; do
not rewrite this corpus from the candidate merely to make a failing gate pass.
