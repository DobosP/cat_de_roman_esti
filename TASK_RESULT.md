# V39 beginner mastery result

Commit: `4592d6e` (`feat(web): add derived beginner mastery`)

Implemented bounded, monotonic starter progression for Intrusul and Perechi:

- starter boards remain active until the first positive non-daily terminal score or three non-daily completions;
- daily runs never advance mastery;
- legacy/imported histories migrate beginner-safely;
- imports merge attempts by bounded maximum and wins by logical OR;
- progress survives the 50-entry recent-history window;
- malformed history falls back to starter eligibility;
- existing game/recent/puzzle caps and the v2 export schema remain unchanged.

Verification:

- focused score-history suite: 8/8 passed;
- full frontend suite: 18/18 files passed;
- frontend lint: passed;
- frontend typecheck: passed;
- frontend production build: passed (117.90/120 KiB gzip);
- static/web pytest: 16/16 passed;
- `git diff --check`: passed.

No documentation, server/session code, TTL, or capacity behavior changed. The
legacy unknown-completion marker intentionally migrates as one non-winning
attempt, and complete new-format progress fields are authoritative so imported
attempt counts retain max-merge semantics.
