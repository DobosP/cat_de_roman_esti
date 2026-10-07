#!/usr/bin/env python3
"""check_docs.py <repo-root> [--all] [--self-test] — fleet doc gate for tracked markdown.

Reports dead relative links, stale model-era terms, retired `ops` verbs, and orphan docs
under `docs/`, over the markdown `git ls-files` tracks. History is skipped by default and never
affects the exit code (`--all` scans it for reporting only): the history dirs (ADRs, handoffs,
journals, sessions, archive, fixtures), WORKLOG/CHANGELOG, and any file with a date ANYWHERE in
its name — leading, trailing, or month-only.

Two guards keep the term checks honest, both reading the previous line as well as the current one:
a term named in order to forbid it is not stale usage, and `ops resume` on a line about the
proposed `ops halt` kill switch is not the retired session verb.

Orphan detection is transitive: a doc is reachable when SOME chain of links leads to it from
`README.md`, `AGENTS.md` or `docs/agent-map.md` — through a hub index, or through a link to the
directory that contains it — so organising docs behind a hub does not orphan them.

Lives in the repo (not `~/work/_temp/`) because scratch is deleted when a branch lands
(ADR-0037/0028) and this gate is part of the docs definition of done
(`docs/29-doc-governance.md` §8). Stdlib only.
"""
import os
import re
import subprocess
import sys

HIST = re.compile(
    r'(^|/)(docs/adr|decisions|adr|handoffs|handover|reviews|sessions|tasks|log|logs|runs'
    r'|archive|_archive|app-sessions|fixtures)(/|$)'
    r'|(^|/)(WORKLOG\.md|CHANGELOG\.md)$'
    # A date anywhere in the file name marks a dated record: leading (2026-07-18-design.md),
    # trailing (architecture_audit_2026-06-16.md) or month-only (live_validation_2026-05.md).
    r'|(^|/)[^/]*\d{4}-\d{2}(-\d{2})?[^/]*\.md$',
    re.I,
)
STALE = re.compile(
    r"\b(opus 4(\.\d)?|sonnet 4(\.\d)?|claude 3(\.\d)?|claude-3|claude-opus-4|claude-sonnet-4"
    r"|gpt-4o?\b(?!-mini-tts)|gpt-5(?:\.[0-5])?(?![\w.])|gpt-6|o3(-mini|-pro)?\b|o4-mini"
    r"|haiku 3(\.\d)?|claude-fable-5(?!-1)|fable 5\b(?!\.)|claude 5\.0)",
    re.I,
)
LINK = re.compile(r'(?<!\!)\[[^\]]*\]\(([^)\s#]+)(#[^)]*)?\)')
RETIRED = re.compile(
    r'(?<![-\w])ops(?:\.ps1)?\s+(resume|pickup|transfer|takeover|host|coordinator|canary'
    r'|tabs|tasks|status|list|new|open|reopen|close|scope|checkpoint|snapshot|stop|park'
    r'|update|provider-update|pin|ui)(?=[\s`.,;:!?)]|$)'
    r'|\bsync\s+--handoff\b',
    re.I,
)
# `ops resume` is also the inverse of the proposed `ops halt` kill switch (vault
# areas/agent-delegation.md): a line about halting is not the retired session verb.
RETIRED_OK = re.compile(r'retired|exit 2|ops halt', re.I)
# A term named in order to forbid it is not stale usage: the doc convention's own wording rules
# quote "Fable 5"/"GPT-6" as names never to write. The guard also reads the previous line, because
# a prohibition often wraps ("… — never \"Fable 5\", \"Claude 5.0\",\n\"GPT-6\", or any invented name.").
STALE_OK = re.compile(r'\bnever\b|\bno longer\b|\bretired\b|\bstale\b', re.I)

SELF_TEST_CLEAN = [
    "gpt-5.6-sol", "gpt-5.6-terra/medium", "gpt-5.6-luna", "claude-fable-5-1",
    "gpt-4o-mini-tts", "Fable 5.1", "claude-opus-5", "claude-sonnet-5",
    "claude-haiku-4-5-20251001", "Haiku 4.5", "ran gpt-5.", "a gpt-5.6 run", "photo3",
]
SELF_TEST_STALE = [
    "gpt-5.5", "gpt-5.4-mini", "gpt-5", "gpt-5.0", "claude-opus-4-8", "Opus 4.1",
    "Fable 5 ", "GPT-6", "o3-mini", "Claude 5.0", "gpt-4o", "claude-fable-5",
    "Sonnet 4", "claude 3.5", "the o3 model",
]
# Retired-verb false positives the ADR-0104 alternation must NOT catch: a bare `agent-ops` hostname
# followed by an ordinary word, "ops status file" as prose about a document, and "ops update-foo".
RETIRED_CLEAN = [
    "agent-ops scope: <id> (<kind>)", "the agent-ops status doc", "run ops update-foo instead",
    "the ops.psx wrapper", "an agent-ops parking policy",
]
RETIRED_STALE = [
    "./ops tabs", "`ops park`", ".\\ops.ps1 park", "ops scope main --workspace",
    "ops new claude api-review", "ops pin TAB", "ops resume", "sync --handoff",
]


def self_test():
    guard_doc = ['names are never written as "Fable 5", "Claude 5.0",', '"GPT-6", or any invented name.']
    for idx in range(len(guard_doc)):
        assert guarded(guard_doc, idx, STALE_OK), f"prohibition guard missed line {idx}"
    assert not guarded(['ran on Opus 4.1 today'], 0, STALE_OK), "guard must not exempt plain usage"
    for case in SELF_TEST_CLEAN:
        m = STALE.search(case)
        assert m is None, f"false positive: {case!r} matched {m.group(0)!r}"
    for case in SELF_TEST_STALE:
        assert STALE.search(case), f"missed stale term: {case!r}"
    for case in RETIRED_CLEAN:
        m = RETIRED.search(case)
        assert m is None, f"false positive: {case!r} matched {m.group(0)!r}"
    for case in RETIRED_STALE:
        assert RETIRED.search(case), f"missed retired verb: {case!r}"
    print("self-test ok")
    return 0


def tracked_markdown(root):
    out = subprocess.run(
        ['git', '-C', root, 'ls-files', '*.md', '**/*.md'],
        capture_output=True, text=True,
    ).stdout.split()
    return sorted(set(out))


def read(path):
    try:
        return open(path, encoding='utf-8', errors='replace').read()
    except OSError:
        return ''


def guarded(lines, index, pattern):
    """True when this line or the one above it marks the term as forbidden/retired."""
    return any(pattern.search(lines[j]) for j in (index, index - 1) if j >= 0)


def scan(root, files):
    dead, stale, retired = [], [], []
    for f in files:
        p = os.path.join(root, f)
        lines = read(p).splitlines()
        for i, line in enumerate(lines, 1):
            for m in LINK.finditer(line):
                target = m.group(1)
                if re.match(r'^[a-z]+:', target) or target.startswith('mailto'):
                    continue
                resolved = os.path.normpath(os.path.join(os.path.dirname(p), target))
                if not os.path.exists(resolved):
                    dead.append(f"{f}:{i}: {target}")
            if not guarded(lines, i - 1, STALE_OK):
                for m in STALE.finditer(line):
                    stale.append(f"{f}:{i}: {m.group(0)}")
            if RETIRED.search(line) and not guarded(lines, i - 1, RETIRED_OK):
                retired.append(f"{f}:{i}: {RETIRED.search(line).group(0)}")
    return dead, stale, retired


def find_orphans(root, files):
    """A doc is an orphan when no chain of links reaches it from an entry point.

    Reachability is transitive: README.md -> docs/compliance/README.md -> the seven
    compliance docs leaves none of them orphaned. A hub index is a legitimate way to
    organise docs, so only genuinely unreachable files are reported.
    """
    entries = ['README.md', 'docs/agent-map.md', 'AGENTS.md']
    candidates = [f for f in files if re.match(r'^docs/.*\.md$', f)]
    reachable, frontier = set(), [e for e in entries if os.path.exists(os.path.join(root, e))]
    seen = set(frontier)
    while frontier:
        text = ''.join(read(os.path.join(root, f)) for f in frontier)
        frontier = []
        for f in candidates:
            if f in reachable:
                continue
            ancestors = [f.rsplit('/', i)[0] for i in range(1, f.count('/') + 1)]
            if (f in text or os.path.basename(f) in text
                    or any(a in text for a in ancestors)):
                reachable.add(f)
                if f not in seen:
                    seen.add(f)
                    frontier.append(f)
    return [
        f"{f}:1: unreachable from README.md, AGENTS.md or docs/agent-map.md (no link chain)"
        for f in candidates
        if f not in reachable and f != 'docs/agent-map.md'
    ]


def section(title, rows):
    print(f"\n## {title}")
    print("\n".join(rows) or "(none)")


def main(argv):
    if '--self-test' in argv:
        return self_test()
    positional = [a for a in argv if not a.startswith('-')]
    if not positional:
        print("usage: check_docs.py <repo-root> [--all] [--self-test]", file=sys.stderr)
        return 2
    root = os.path.abspath(positional[0])
    include_all = '--all' in argv
    every = tracked_markdown(root)
    live = [f for f in every if not HIST.search(f)]
    history = [f for f in every if HIST.search(f)]

    dead, stale, retired = scan(root, live)
    orphans = find_orphans(root, live)

    print(f"# check_docs {root}")
    print(
        f"files={len(live)} dead_links={len(dead)} stale_terms={len(stale)} "
        f"retired_verbs={len(retired)} orphans={len(orphans)}"
    )
    section("dead links", dead)
    section("stale model terms", stale)
    section("retired ops verbs", retired)
    section("orphan docs", orphans)

    if include_all:
        h_dead, h_stale, h_retired = scan(root, history)
        print("\n## history (report only)")
        print("\n".join(h_dead + h_stale + h_retired) or "(none)")

    return 1 if (dead or stale or retired or orphans) else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
