"""Run the unchanged fleet checker in containers without Git metadata."""
import os
import sys
sys.dont_write_bytecode = True
import check_docs

root = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else '.')
skip = {'.git', 'node_modules', '.gate', '.vitest', 'dist', 'test-results'}
every = []
for base, dirs, files in os.walk(root):
    dirs[:] = sorted(d for d in dirs if d not in skip)
    every.extend(os.path.relpath(os.path.join(base, f), root) for f in files if f.endswith('.md'))
live = sorted(f for f in every if not check_docs.HIST.search(f))
if not live or not {'README.md', 'AGENTS.md'} <= set(live):
    raise SystemExit('docs gate: empty scan or missing required entry points')
dead, stale, retired = check_docs.scan(root, live)
orphans = check_docs.find_orphans(root, live)
print(f'files={len(live)} dead_links={len(dead)} stale_terms={len(stale)} retired_verbs={len(retired)} orphans={len(orphans)}')
for title, rows in [('dead links', dead), ('stale model terms', stale), ('retired ops verbs', retired), ('orphan docs', orphans)]:
    check_docs.section(title, rows)
raise SystemExit(bool(dead or stale or retired or orphans))
