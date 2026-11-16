# Offline all-boards view diff

Compare two native private bundles for [ADR-0231](../../../docs/adr/0231-v5-dumps-words-and-model-candidates.md) and [S7](../../../docs/CONTENT_LOOP.md#s7-assembly). Use the exact baseline and candidate export bytes and their independent SHA-256 digests. Keep both inputs and the report in private campaign scratch.

```sh
go -C go-backend build -o "$CAMPAIGN/cat-board-view-diff" ./cmd/cat-board-view-diff
"$CAMPAIGN/cat-board-view-diff" \
  --baseline "$BASE_BUNDLE" --baseline-sha256 "$BASE_SHA256" \
  --candidate "$CANDIDATE_BUNDLE" --candidate-sha256 "$CANDIDATE_SHA256" \
  > "$CAMPAIGN/board-diff.json"
```

The report (schema `cat-board-view-diff-2`) lists additions and disturbances in
stable game and ID order. A baseline row absent from the candidate is a disturbance.
Its report entry carries the old view hash for S7 follow-up. A changed row identifies
the changed view fields. Selection scores, ranks, tickets and source grouping have
their own changes list. The compact report contains no answer or recipe payloads.

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

| Game | Counted board view | Diagnostics |
| --- | --- | --- |
| Cald sau Rece | Target and ordered top 100 reachable KG concept IDs, using the live profile and score. Ties break by distance, label and ID after rank. Alternate inputs are outside the top-100 metric. | Top-100 labels, distances, ranks, closeness and temperature, the target display and the displayed reachable population count. |
| Lanțul Cuvintelor | Endpoints, declared par, actual shortest distance and the complete directed shortest-route DAG. | Route labels, full captions and displayed short captions, the target display and native menus, including detours, at each shortest-route prefix. Routes exceeding 2,048 menus fail the comparison. |
| Alchimie | Real native recipe projection including compatible reviewed extensions, par, routes, displayed concepts and recipe link captions. | None. |
| Conexiuni | Visible tile order and labels, group membership and labels, clue patterns and the native content fairness screen. | None. |
| Intrusul and Perechi | Exact serving payloads and visible tile labels. | None. |

Category, category label and difficulty are counted for all six games.

## Disturbed boards and diagnostics

The S7 comparison, the one-word preview and the paired re-blind share one
definition. A board is disturbed when a counted field changes. A Cald board is
disturbed when its target or its ordered top-100 ID list changes (owner decision,
2026-11-16). A Lanț board is disturbed when its endpoints, declared par, shortest
distance or shortest-route topology changes
([ADR-0231](../../../docs/adr/0231-v5-dumps-words-and-model-candidates.md) decision 8).

A changed diagnostic never disturbs a board. One new word enlarges the reachable
population of every Cald board and shifts some closeness and temperature values.
Those boards appear in `diagnostic_changes` with their changed field names and
before and after hashes. A board can appear in both lists. Together `disturbed` and
`diagnostic_changes` name every board whose native view changed. For S7, re-blind
every disturbed board and replay every board of both lists over HTTP under the
content loop. Schema `cat-board-view-diff-1` S7 reports counted the diagnostic
fields as disturbances. Closeout refuses them.

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

The preview counts disturbed boards exactly as S7 does. A board removed from
reachable stock counts as disturbed. The report sets `one_word_dry_run.hold` when
more than 10 boards are disturbed across all six games. Source evidence and
registry order are checked by the link installer.

## Paired re-blind of disturbed existing Cald boards

A blind critic plays each disturbed existing Cald board on the candidate. This mode
replays the critic's typed guesses with the native Cald service on both exact
bundles and writes a `cat-v5-board-reblind-compare-1` receipt.

```sh
"$CAMPAIGN/cat-board-view-diff" --reblind-compare \
  --baseline "$BASE_BUNDLE" --baseline-sha256 "$BASE_SHA256" \
  --candidate "$CANDIDATE_BUNDLE" --candidate-sha256 "$CANDIDATE_SHA256" \
  --baseline-commit "$BASE_COMMIT" --candidate-commit "$CANDIDATE_COMMIT" \
  --view-diff "$CAMPAIGN/board-diff.json" --view-diff-sha256 "$DIFF_SHA256" \
  --evidence-root "$CAMPAIGN" --transcripts "$CAMPAIGN/board-reblind-list.json" \
  > "$CAMPAIGN/board-reblind-compare.json"
```

The transcript list has the schema `cat-v5-board-reblind-compare-input-1` and a
`boards` array. Each row gives `game` (`contexto`), `id` and a `transcript` object
with `path` and `sha256`. Paths use forward slashes and stay below the evidence
root. Each transcript is the object that closeout reads: `game`, `id`, `view_sha256`
(the view diff `after_sha256`), `thread_id`, `verdict` and `play`. A play step whose
`guess` member is a string is one typed guess, in play order. Every other step is
feedback and is not replayed.

Each receipt row carries these values.

| Field | Meaning |
| --- | --- |
| `candidate_best_rank`, `baseline_best_rank` | Best native rank among the scored guesses on each build. An unknown word or an unconfirmed spelling suggestion costs no attempt and is not scored. Replay stops at the native win. |
| `won_candidate`, `won_baseline` | Whether the same guesses win each build. |
| `k` | Number of concepts present only in the candidate that rank above the candidate's best guess on that board. Each one moves an unchanged guess down one rank. |
| `verdict` | `win` when the candidate is won. Otherwise `worse` when the same guesses win the baseline. Otherwise `no-worse` when `candidate_best_rank <= baseline_best_rank + k`. Otherwise `worse`. A board whose target differs between the two bundles is refused. |
| `stock_quality` | True when neither build is won. Closeout copies these boards to the landing receipt for the owner queue. |

The receipt binds both commit IDs, both bundle digests, the view diff digest, each
board ID with its before and after view digests, the critic thread and each
transcript path and digest. It contains no guess text. Rows are in stable board ID
order and the same inputs give the same bytes. The mode rebuilds each board's
counted view from both bundles and refuses a view diff row that differs. It refuses
a board outside the diff's changed Cald disturbances, a repeated board or
transcript, a transcript bound to another view and a play in which either build
scores no guess. A `worse` row is recorded evidence and the command still exits 0.

Limits: 512 boards, 1 MiB per transcript and for the list, 8 MiB for the view
diff, 512 play steps, 64 typed guesses and 256 bytes per guess.

## Threat model

The orchestrator owns the bundles, the view diff, the transcripts and this tool's
output. The tool guards against mixed-up or edited files between steps. It cannot
prove where a file came from.

- SHA-256 digests bind exact bytes. The two commit IDs are recorded labels. The
  tool has no Git access. Closeout checks them and compares both bundle digests
  with the bundles committed at those IDs.
- The paired verdict can only relax the blind-win rule for a disturbed existing
  Cald board, and only when closeout also finds the two reviewer signatures for
  that board's top-100 change. New boards keep the absolute win rule. Lanț and the
  other games keep the blind pass rule. This tool enforces the Cald-only scope.
  [Closeout](../../../scripts/content_v5/CLOSE_LANDING.txt) enforces the rest.
- The replay proves what the typed guesses score on both builds. It cannot prove
  that the critic was blind, independent or the real author of the transcript.
  Those stay operator and reviewer obligations.
- A critic who guesses a candidate-only word gains nothing on the baseline, where
  that word is unknown and unscored.
- `os.Root` confines transcript paths to the evidence root and refuses symlinks
  that leave it. The leaf must be a regular file.
- All inputs are size-bounded and read once. The command works offline and starts
  no HTTP service. The replay uses one private native session per board and build
  and removes it.

## Input and report boundaries

Pass independently recorded digests for trusted native exports or a qualified
unapproved candidate. SHA-256 binds exact bytes. A digest alone supplies neither
source provenance nor review approval. Inputs have a 32 MiB ceiling, must be regular
files and must pass strict JSON, native bundle decoding and board-shape checks. Input
bytes are read once and checked before graph or game work. The command works offline,
never starts an HTTP service and writes only its report to stdout. Redirect to a
private campaign path. Bundle files contain private answers and must stay private.
