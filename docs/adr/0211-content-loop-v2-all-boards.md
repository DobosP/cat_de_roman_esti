# ADR-0211: V2 content loop for all six games' boards

Date: 2026-10-22
Status: proposed — approved design defaults recorded; Phase A procedure awaits Paul's review

## Context

Paul approved the [V2 design](../reviews/content-loop-v2-design-20261022.md) section9 defaults,
with B1 first, and explicitly authorized this one-time Phase A edit of CONTENT_LOOP.md.
[ADR-0210](0210-curation-waves-and-staged-stock-landing.md) governs the staged1,083 source packages,
owner exclusions and test-pin packet. [The read-only review](../reviews/content-loop-review-20261022.md)
qualifies evidence tiers/counts; source acceptance does not establish playable boards or integration.
This ADR extends ADR-0188/0210; it does not rewrite preserved V1 decisions or signed evidence.

## Decision recorded for procedure review

- [CONTENT_LOOP.md](../CONTENT_LOOP.md) makes boards/targets across all six games the outcome;
  M0–M9 covers need map, bounded KG mining, compat index, lint, blind critic, freeze, two review
  rounds, landing packet and recording. Vocabulary needs a named board_ref or curation.
- Adopt design defaults: batch≤24boards/first≤4,24ticks/20commits,seven-day waiting expiry,at least
  one curation in every three landings while stock remains. One frozen batch until land/expiry.
- Critic is a pre-review filter, never a third signer. Fixed independent factual/quality reviewers
  use own subprocesses and reviewer-chosen sources, sealed author URLs, ordered signed_at/read
  receipts,≤20% identical rationales and no reviewer-name occurrence in M1–M5 artifacts. Keep raw native schemas unchanged;
  scratch sidecars enforce added process requirements, not an invented native implementation.
- Add rubric I/J for Intrusul/Perechi; JS mapping remains a separate code task. Proposed Perechi
  margin.15,Alchimie productive-pair40%,Lanț typed-edge50%,Conexiuni cross-link bands and Cald
  gastronomie freeze stay WARN for B1/C1/B2; review measured results for later ratification.
- Class P pays quick/extensions regeneration, corpus, authorities and full gates/world inheritance;
  class G pays all4a–4i. No light path; do not mix KG and boards. Derived123-source/336-board freeze
  and discovery-world scope stay unchanged;83 historical Conexiuni FAIL repairs are separate.
- Separate pins commit permits only moved expectations in httpgolden selection tests,contentops
  board/approved counts and contexto inbound maps, with old→new and git show --stat. Owner reviews.
- IDs b1,c1,b2 use content/v2-<id>-<slug>,python-http-parity-v2-<id>.json.gz,reviewedV2<ID>() and
  v2<id>_selection_test.go. Derive next authored-vK from current sources,currently v13 next.
- Order **B1→C1→B2**: up to4 Lanț pack chains;≥20 existing-owner morphology families from V1.38–42
  including Avion/Cinematograf/Interfon;then up to20 multi-game boards. Mănăstire/Sucitor rows name
  snapshot rebuilds;bare sucitoare stays excluded and Ie never ii/iei. All earlier exclusion hits
  stay held with file:line. V1.33 needs re-research,V1.14 is reapplied,never merged.
- Keep read-only helpers under ~/work/_temp/content-loop/miner/; porting after B2 is separate code.
  Evidence under ~/work/_temp/content-loop/evidence/<id>/ is preserved and exempt from routine
  scratch sweeps; NAS SHA-verified copy is mandatory before any owner-operated deletion.
- The old automation stays paused permanently. Only after this procedure is on main and Paul says
  start may Phase B migrate compact state/append decisions and be scheduled as cat-content-v2.
- Host Go1.27.3 from /usr/local/go is required; no toolchain/dependency or runtime changes here.
- **Claude Code landing rule:** the loop stops at waiting:land? (pins packet + gates). Paul's Claude
  Code session independently reviews,merge --ff-only,pushes (ADR-0014),copies evidence to NAS and
  deletes the branch/worktree (ADR-0037). The loop never merges,pushes or deletes. Its owner word
  land answers land? only;go/drop answers review only;continue starts an interactive burst.

## Phase A boundary and executable prerequisite

Only the seven owner-allowlisted documentation files and read-only scratch helpers are drafted;
no content,fixture,runtime,pin,gate or automation mutation and no Phase B run. Stop at
waiting:V2 procedure review with the exact commit and check results.
Adding rubric I/J changes the compiled reviewed digest (contentbuild.RubricSHA256 and rail source
bindings). Phase A cannot alter those pins/catalogs/authorities. The required checks are run and
any rubric-drift failures are recorded in the review packet as BLOCKED. A separate owner-authorized
rubric-pin/authority transition must be reviewed and landed before executable Phase B gates can
be green; this proposed procedure is not that transition and never waives a check.

## Phase A validation record

Executed from the isolated docs/content-loop-v2 worktree with host go1.27.3:
- cat-doc-check --root .. --inventory docs/tracked-markdown.json: PASS.
- python3 ~/work/agent-ops/scripts/check_docs.py .: PASS.
- git diff --check: PASS.
- Requested go test -count=1 over doccheck/contentbuild/contentops/contentrails/httpgolden:
  doccheck and httpgolden PASS; contentbuild/contentops/contentrails FAIL after the requested
  rubric edit. First error: installed_bundle_build_test.go:22: reviewed rubric digest drift.
  Related ranking/derived metadata and rail binding failures are retained in scratch checks.
  BLOCKED: native content gate suite → reviewed rubric digest drift; no pin or generator repair.
Scratch results: ~/work/_temp/content-loop/miner/phase-a-checks-final/ (initial run also retained).
Helper smoke proofs and limitations are retained under ~/work/_temp/content-loop/miner/.
This is a documentation proposal with a recorded executable prerequisite, not a green landing.
