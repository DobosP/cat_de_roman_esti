# Native source content builder

`go run ./cmd/cat-content export --root .. --check` rebuilds the private export
from eight bounded source files and compares the bundle and digest authority byte
for byte. `validate`, `validate-fixture`, and `validate-pack` run native source
gates; `--kg`/`--pack` support prospective synthetic fixtures. No server or public
solution endpoint is created. The standalone validators do not install content.

The eight source digests, required reviewed rubric, graph records/defaults, Unicode normalized index,
reviewed display labels, selector scores/weights, reserve definitions, frozen
quick identities, captions, mechanics/history fingerprints, manifest and metadata
counts are reconstructed in Go. Current output is exactly the pre-migration
`f2f8a629f3366a8da6984f608d01dd2ef2354f6de857f0db8b1268047fb6de88` export.
The historical digest-file header is retained to preserve its frozen bytes.

`rules_unicode15.json` is a separate private rule input: Unicode 15 NFKD/fold,
casefold, letter and full uppercase tables; authored category/caption/Contexto
rules; exact label repairs; legal/OpenAPI templates. The migration bootstrap
read the original rule modules with Python 3.12 and Unicode 15, without reading
`bundled.json`. `rules_provenance.json` records that historical bootstrap and
source-module hashes. Native build/export/validation never calls Python, imports
Django, or depends on the current Go Unicode version. Future rule edits require
reviewing this rule input and its explicit digest authority. Dynamic health,
category, manifest and world fields are rebuilt rather than inherited from
metadata templates. Pinned templates contain no runtime operator credentials.

Three review-authority artifact pins (frozen derived catalog, authored quick
catalog and release reserve) retain the former fail-closed boundary; a new
reviewed version needs an explicit pin update. Graph/pack/ranking identities are
cross-bound from the actual source bytes; copied fixture files must match.
Recipe extension source bindings retain their historical metadata semantics;
entry/core fingerprints and scopes are validated completely and the serving
recipe service only applies additions when actual graph snapshots match.

Tests cover exact frozen bytes/pin/all eight digests, Unicode-version boundaries,
directed puzzle and Contexto distances, sequential Alchimie par, all source
families' mutation failures, independent review gates, source provenance, archived
save fingerprints, and rehashed attempts to overwrite protected recipe cores.

Export writes share `.cat-content-ops.lock` with review operators. The source
build runs after acquiring that lock; both output targets must have regular,
non-symlinked paths. Sibling replacements preserve file modes, synchronize the
files/directories, and restore and byte-verify both original targets on a partial
write or failed post-write freshness check. Native synthetic tests inject each
failure; no reviewed fixture or private bundle is rewritten by those tests.
