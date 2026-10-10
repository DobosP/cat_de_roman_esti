# ADR-0188: Park V1.7 and reset the content loop

Date: 2026-10-10
Status: Accepted. The owner asked for the V1.7 branch to be reviewed and then landed or parked, and for the content-loop prompt to be replaced (Claude Code review session, 2026-10-10).
Supersedes: ADR-0183. Partially supersedes: ADR-0173 (the stay-in-version rule), ADR-0185 (decision 4 and evidence preservation for content waves) and ADR-0186 (failed-evidence preservation for content waves).

## Context

- V1.2–V1.6 together added 3 concepts, 15 links and 38 input forms, and no new rounds
  (`cat-content-ops delta --baseline 17f7da1~1`). V1.7 ran for about three days and proposed one
  input form (leafă → Salariu). It installed nothing, and it left about 634 MiB of receipts on main
  plus about 220 MiB more on `codex/content-v1-7`.
- The branch carries no content that main lacks: the V1.7 data scripts and the pool are already on
  main. It also contains a `.gitattributes` relaxation that makes 2250 whitespace findings pass,
  a change to the AGENTS.md rule for deleting unmerged work, and an ADR-0187 whose owner
  authorization cannot be confirmed from the repository.
- The owner judged the loop's words low in value. A quality review found that common words are
  missing (seasons, days, colours, cardinal directions, common animals). The old process
  allowed only edges between existing nodes, so it could never add them.
- `cat-content-rail all --root .. --check` and `go test ./internal/contentrails` have been red on
  main since 5baf581 (GUI kit sync). The installed rail authorities hash every non-test Go file
  under go-backend and shared-go/authcore, so any non-content Go change makes them stale.

## Decision

1. Park V1.7. `codex/content-v1-7` and `codex/content-v1-7-qualification` are not merged. The
   branches, the worktree and the Codex scratch stay until the owner decides; this ADR deletes
   nothing. ADR-0187 and the AGENTS.md rule change are not adopted.
2. V1.7 content outcome:
   - leafă is an input form of Salariu, not a concept. It returns in a later batch with its full
     non-colliding paradigm.
   - Compot and Sandviș are closed as duplicates of live nodes.
   - Tocător (cutting board), Scrisoare→Plic and Busolă→Nord return as candidates for new
     concepts.
   - The V1.7 pool remains the record.
3. Content waves are batches, judged by player-visible additions. The stay-in-version rule, the
   single-item admission of ADR-0183 and the leafă-first priority no longer bind content waves.
   A wave keeps its pool, a short plain-text README, the review JSON its rails require, and the
   gates in AGENTS.md and agent-testing. It does not create admission, clock or per-attempt
   packets, nested archives or tarballs. `docs/reviews/<wave>` is text-only and holds the files
   the rails bind plus a few small summaries. A
   content wave needs an ADR only if it changes game behaviour or a data schema.
   [CONTENT_LOOP.md](../CONTENT_LOOP.md) is the operating procedure for content waves. Where it is
   more specific than STATUS, the content skill or ADRs 0170–0187, it takes precedence.
4. A content loop changes content data, the files generated from it and the bookkeeping that
   the rails require. Toolchain, GUI, runtime logic, CI, deploy, retention policy and new gates
   are outside its scope. It reports a broken non-content gate as BLOCKED and does not fix it.
5. No content is installed until a separate, owner-approved task makes the rail baseline green
   again and re-anchors the tests that pin the live content bytes (contentbuild/source6_build_test.go
   pins the bundled.json length and SHA), so a content wave can pass without editing `_test.go`.
   Until then the loop does research-only waves.

## Consequences

Independent factual and quality review, the supported graph transaction, private answers,
deterministic bounded sessions and the existing validators and thresholds are unchanged.
Earlier V1.x records remain history.
