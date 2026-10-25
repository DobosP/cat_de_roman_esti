# ADR-0211: V2 content loop for all six games' boards

Date: 2026-10-22
Status: partially superseded by [ADR-0212](0212-bounded-content-workflow-repair.md) for execution,
cadence and Class-P world retention; original V2 quality rules remain accepted. Paul approved the
original procedure on 2026-10-22 with rubric I/J outside the digest-bound rubric

## Context

Paul approved the [V2 design](../reviews/content-loop-v2-design-20261022.md) section 9 defaults,
with B1 first, and authorized this one-time rewrite of CONTENT_LOOP.md.
[ADR-0210](0210-curation-waves-and-staged-stock-landing.md) governs the staged 1,083 source packages,
owner exclusions and test-pin packet. [The read-only review](../reviews/content-loop-review-20261022.md)
qualifies evidence tiers/counts; source acceptance does not establish playable boards or integration.
This ADR extends ADR-0188/0210; it does not rewrite preserved V1 decisions or signed evidence.

## Decision

- [CONTENT_LOOP.md](../CONTENT_LOOP.md) makes boards/targets across all six games the outcome;
  M0–M9 covers need map, bounded KG mining, compat index, lint, blind critic, freeze, two review
  rounds, landing packet and recording. Vocabulary needs a named board_ref or curation.
- Adopt design defaults: batch ≤24 boards (first ≤4), 24 ticks/20 commits, seven-day waiting
  expiry, at least one curation in every three landings while stock remains. One frozen batch
  until land/expiry.
- Critic is a pre-review filter, never a third signer. Fixed independent factual/quality reviewers
  use own subprocesses and reviewer-chosen sources, sealed author URLs, ordered signed_at/read
  receipts, ≤20% identical rationales and no reviewer-name occurrence in M1–M5 artifacts. Keep raw
  native schemas unchanged; scratch sidecars enforce added process requirements, not an invented
  native implementation.
- Rubric I/J for Intrusul/Perechi and the V2 review protocol live unbound in CONTENT_LOOP.md; the
  bound rubric is unchanged (`contentbuild.RubricSHA256` 3fc2d6db…). `docs/CRITIQUE_RUBRIC.md` is
  digest-bound into rankings, the derived catalog, all three rails and the installed authorities,
  so folding I/J into it is a separate owner-authorized class-G transition, never part of a class-P
  landing. JS mapping remains a separate code task. Proposed Perechi margin 0.15, Alchimie
  productive-pair 40%, Lanț typed-edge 50%, Conexiuni cross-link bands and Cald gastronomie freeze
  stay WARN for B1/C1/B2; review measured results for later ratification.
- Paul kept two stricter lexical rules from the draft (2026-10-22): a lexical addition cites its
  own head's DOOM3 flexion table, never another head's, and a qualified compound needs component
  morphology plus separate compound-sense evidence.
- Class P pays quick/extensions regeneration, corpus, authorities and full gates/world inheritance;
  class G pays all 4a–4i. No light path; do not mix KG and boards. Derived 123-source/336-board
  freeze and discovery-world scope stay unchanged; 83 historical Conexiuni FAIL repairs are separate.
- Separate pins commit permits only moved expectations in httpgolden selection tests, contentops
  board/approved counts and contexto inbound maps, with old→new and git show --stat. Owner reviews.
- IDs b1, c1, b2 use content/v2-<id>-<slug>, python-http-parity-v2-<id>.json.gz, reviewedV2<ID>()
  and v2<id>_selection_test.go. Derive next authored-vK from current sources, currently v13 next.
- Order **B1→C1→B2**: up to 4 Lanț pack chains; ≥20 existing-owner morphology families from
  V1.38–42 including Avion/Cinematograf/Interfon; then up to 20 multi-game boards. Mănăstire/Sucitor
  rows name snapshot rebuilds; bare sucitoare stays excluded and Ie never ii/iei. All earlier
  exclusion hits stay held with file:line. V1.33 needs re-research, V1.14 is reapplied, never merged.
- Keep read-only helpers under ~/work/_temp/content-loop/miner/ (pinned by
  phase-a-helpers-manifest.json); porting after B2 is separate code. Helpers and evidence under
  ~/work/_temp/content-loop/ are preserved and exempt from routine scratch sweeps; a NAS
  SHA-verified copy is mandatory before any owner-operated deletion.
- The old automation stays paused permanently. Only after this procedure is on main and Paul says
  start may Phase B migrate compact state/append decisions and be scheduled as cat-content-v2.
- Host Go 1.27.3 from /usr/local/go is required; no toolchain/dependency or runtime changes here.
- **Claude Code landing rule:** the loop stops at waiting: land? (pins packet + gates). Paul's
  Claude Code session independently reviews, merges --ff-only, pushes (ADR-0014), copies evidence
  to the NAS and deletes the branch/worktree (ADR-0037). The loop never merges, pushes or deletes.
  Owner words: land answers land? only; go/drop answers review only; continue starts an interactive
  burst; resume <id> answers a wait Paul's instruction names.

## Landing record

Codex drafted the procedure (9f64dc1e) with I/J added to `docs/CRITIQUE_RUBRIC.md`; that changed
the bound digest and turned contentbuild, contentops and contentrails red (reviewed rubric digest
drift). A three-lens landing review found the fix: keep the rubric byte-identical to main
(sha256 3fc2d6db…) and carry I/J unbound in CONTENT_LOOP.md. It also scoped the independence guard
to the review shapes it can read, added owner words for every wait and `-count=1` to the gate
tests. Checks on the landed head, from the task worktree with host go1.27.3 (`GOTOOLCHAIN=local`):
`go -C go-backend test -count=1` over doccheck, contentbuild, contentops, contentrails and
httpgolden: ok; cat-doc-check --root .. --inventory docs/tracked-markdown.json, check_docs.py and
git diff --check: PASS.

## Consequences

- The V2 loop can start from a green M0 baseline once Paul says start; this landing schedules nothing.
- I/J apply through explicit critic and reviewer briefs, not lints or the bound rubric, until the
  separate rubric transition lands.
- The independence guard runs on M6, round 2 and curation step 3 through native files or signed
  sidecars; curation step 3 needs a Claude-reviewed helper update before C1.
