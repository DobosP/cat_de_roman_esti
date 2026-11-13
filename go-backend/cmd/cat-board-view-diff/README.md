# Offline all-boards view diff

Compare two native private bundles for [ADR-0231](../../../docs/adr/0231-v5-dumps-words-and-model-candidates.md) and [S7](../../../docs/CONTENT_LOOP.md#s7-assembly). Use the exact baseline and candidate export bytes and their independent SHA-256 digests. Keep both inputs and the report in private campaign scratch.

```sh
go -C go-backend build -o "$CAMPAIGN/cat-board-view-diff" ./cmd/cat-board-view-diff
"$CAMPAIGN/cat-board-view-diff" \
  --baseline "$BASE_BUNDLE" --baseline-sha256 "$BASE_SHA256" \
  --candidate "$CANDIDATE_BUNDLE" --candidate-sha256 "$CANDIDATE_SHA256" \
  > "$CAMPAIGN/board-diff.json"
```

The report lists additions and disturbances in stable game and ID order. A baseline
row absent from the candidate is a disturbance. Its report entry carries the old
view hash for S7 follow-up. A changed row identifies the changed view fields.
Selection scores, ranks, tickets and source grouping have their own changes list.
The compact report contains no answer or recipe payloads.

For ranked pack games, the finite inventory follows `pack.Pack.PickSeeded` and
`PickDaily`. Both restrict ranked pools to `PilotEligible`. Native ranking marks
held reserve rows ineligible. The report also records the approved and ineligible
pack totals. Quick rows come from the exact derived and authored catalog in
`content.Content.Boards`. Native export removes the reserved Quick definitions.
`catalog.Catalog.PickSeeded` and `PickDaily` apply the preferred shelf. A below-shelf
row is selectable if its category has a normal or starter pool where at most four
preferred sources compete and its own source is absent from those competitors.
Each of those preferred sources can be selected once to fill the previous-game
source history. The report includes stored and unreachable Quick counts.
Procedurally mined rounds have no finite catalog ID.

The current baseline has 923 selectable finite IDs.

| Game | Selectable | Approved pack or stored Quick | Excluded |
| --- | ---: | ---: | ---: |
| Alchimie | 68 | 80 | 12 |
| Conexiuni | 95 | 257 | 162 |
| Cald sau Rece | 257 | 265 | 8 |
| Intrusul | 201 | 226 | 25 |
| Lanțul Cuvintelor | 126 | 126 | 0 |
| Perechi | 176 | 192 | 16 |

| Game | Board view |
| --- | --- |
| Cald sau Rece | Target and ordered top 100 reachable KG concept IDs, using the live profile and score. Ties break by distance, label and ID after rank. S7 includes top-100 labels, distances, ranks, closeness and temperature, and the target display. S7 also includes the displayed reachable population count. Alternate inputs are outside the top-100 metric. |
| Lanțul Cuvintelor | Declared par, actual shortest distance and complete directed shortest-route DAG with labels, full captions and displayed short captions. S7 also compares native menus, including detours, at each shortest-route prefix. Routes exceeding 2,048 menus fail the comparison. |
| Alchimie | Real native recipe projection including compatible reviewed extensions, par, routes, displayed concepts and recipe link captions. |
| Conexiuni | Visible tile order and labels, group membership and labels, clue patterns and the native content fairness screen. |
| Intrusul and Perechi | Exact serving payloads and visible tile labels. |

## One-word preview before source pins

Use the link installer to prepare the first S2-sourced backlog word in registry
order, then pass the exact prospective KG and rederived pack. The baseline source
checkout must still match the bundle.

```sh
"$CAMPAIGN/cat-board-view-diff" \
  --baseline "$BASE_BUNDLE" --baseline-sha256 "$BASE_SHA256" \
  --one-word-dry-run --baseline-root "$BASE_ROOT" \
  --prospective-kg "$NEW_KG" --prospective-kg-sha256 "$NEW_KG_SHA256" \
  --prospective-pack "$NEW_PACK" --prospective-pack-sha256 "$NEW_PACK_SHA256" \
  > "$CAMPAIGN/one-word-board-diff.json"
```

The preview checks for one additive KG concept and four to eight incident
non-distractor links. It validates the rederived pack against native graph mechanics,
rebuilds native ranks and V38 derived and authored Quick catalogs, verifies reserve
identities and projects native captions and recipes. It reproduces the baseline
catalogs and views against the sealed bundle before comparing the prospective
inputs. Pack IDs and frozen payload fields must retain their baseline identities.
The preview produces no serving bundle and updates no source pin. The report binds
both input SHA-256 digests.

The dry-run metric counts Cald changes in the ordered top-100 IDs. It counts
Lanț changes in shortest-route topology. S7 Cald feedback and display fields and
Lanț route captions, labels and menus appear as diagnostics in dry mode.
A board removed from reachable stock counts as disturbed. The report sets
`one_word_dry_run.hold` when more than 10 boards are disturbed across all six
games. Source evidence and registry order are checked by the link installer.
For S7, re-blind and replay every disturbed board under the content loop.

## Input and report boundaries

Pass independently recorded digests for trusted native exports or a qualified
unapproved candidate. SHA-256 binds exact bytes. A digest alone supplies neither
source provenance nor review approval. Inputs have a 32 MiB ceiling, must be regular
files and must pass strict JSON, native bundle decoding and board-shape checks. Input
bytes are read once and checked before graph or game work. The command works offline,
never starts an HTTP service and writes only its report to stdout. Redirect to a
private campaign path. Bundle files contain private answers and must stay private.
