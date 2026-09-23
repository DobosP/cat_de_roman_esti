# V1.0.1 hardening review

Valid until: the next change to the reviewed 1.0.1 source — then treat as history.

Base: V1 testing release `2ba8a8b` ([ADR-0158](../../adr/0158-v1-testing-release.md)).
Decision: [ADR-0159](../../adr/0159-v1-0-1-testing-hardening.md). Current gates: [STATUS](../../STATUS.md).
Condensed evidence: [findings.json](findings.json).

## Method

Ten independent reviewers covered the lobby and daily flow, recovery and storage, phone
layout and accessibility, backend selection, content repairs, current selectable stock,
the tester guide and docs, test quality, first-minute UX and release plumbing. Each
finding was re-judged by separate verifiers that tried to refute it by running or
reading the code (two lenses for blocker/major, one otherwise). 55 findings were raised:
51 survived and 4 were refuted. A judge grouped the survivors into eight parallel
work packages, each built in its own worktree and approved by an independent reviewer
that reran the tests. A second, integration-level review of the merged result found 14
more confirmed issues (all polish/minor), and a completeness audit mapped every
original finding to the code.

## Outcome

- Fixed: 42 of the 51 original findings, including two completed during integration
  polish (long words on phones, ISO dates in history). Nine are deferred below.
- Integration review: 13 of 14 confirmed items fixed. The lowercase-label allowlist
  still lacks a regression test that would catch a new lowercase brand name; the
  display rule itself is covered.
- No content artifact changed: every fixture digest in STATUS is unchanged.

## Deferred (with reasons in findings.json)

- Missing diacritics in served descriptions and "roman"/"român" confusion; the
  unidiomatic repaired Ateneu description; label spellings (Herta Müller, Mica Unire).
- The false Toma Caragiu–Reconstituirea casting edge (removing it alone turns the pack
  validator red for one Lanț board, so it needs a bound proposal and review).
- Lanț `lt_personalitati_186` solvable only through generic nodes, and off-theme
  single-board Conexiuni Limbă/Geografie Greu shelves (selection decisions).
- Alchimie Greu start latency on shelves without a curated board (documented; a time
  cap would break deterministic dailies).
- Post-V1 history tests that re-hash live content (developer-only; refactor with the
  next content wave).

Each content item re-pins KG, pack or ranking digests, so they belong in one reviewed
content wave rather than this code hardening.

## Limits

All browser evidence is Chromium (Microsoft Edge) emulation on Windows. Physical phones,
Safari/WebKit and human enjoyment are untested; the tester guide's same-Wi-Fi session is
the next step.
