#!/usr/bin/env bash
# Focused inner-loop checks only. Invoke through the trusted owning shell gate.
set -euo pipefail
[ "$PWD" = /work ]
out=/work/.gate/shell/game-renovation
mkdir "$out"
node --input-type=module - <<'JS' > "$out/context.json"
import fs from 'node:fs';
import assert from 'node:assert/strict';
const context = JSON.parse(fs.readFileSync('.gate/wrapper-current.json'));
assert.equal(context.target, 'shell');
assert.equal(context.sha, process.env.GATE_SHA);
assert.equal(context.tree_sha256, process.env.GATE_TREE_SHA256);
assert.equal(context.operator, 'agent:codex');
console.log(JSON.stringify(context));
JS
failed=0
run() {
  local label=$1
  shift
  local rc=0
  timeout 600s "$@" > "$out/$label.stdout.log" 2> "$out/$label.stderr.log" || rc=$?
  printf '%s\n' "$rc" > "$out/$label.exit"
  printf '%s: exit %s\n' "$label" "$rc"
  [ "$rc" = 0 ] || failed=1
}
cd /work/frontend
run typecheck npm run typecheck
run tools-typecheck node scripts/native-tsc.mjs --project tsconfig.tools.json --noEmit
run focused node --test tests/alchimie-mode.test.mjs tests/home-card-blur.test.mjs tests/game-help.test.mjs tests/gui-route-budgets.test.mjs tests/gui-style-audit.test.mjs tests/v1-daily-intent.test.mjs
run scores node --test tests/score-receipts.test.mjs tests/scores-nondaily-history.test.mjs tests/v1-record-on-loss.test.mjs tests/v39-local-daily-circuit.test.mjs tests/v42-meta-loop.test.mjs
run lint npm run lint
run build npm run build
cd /work
run docs go -C go-backend run ./cmd/cat-doc-check --root .. --inventory docs/tracked-markdown.json
if [ "$(cat "$out/build.exit")" = 0 ]; then
  run budgets node --input-type=module - <<'JS'
import { readFileSync } from 'node:fs';
import { createRequire } from 'node:module';
import { appRoutePaths, alchimieModeBindings, portedSetBindings, measureProfile } from './scripts/gui-route-budgets.mjs';
import * as api from './frontend/node_modules/@roedu/web-kit/budget/index.mjs';
const require = createRequire('/work/frontend/package.json');
const ts = require('@typescript/typescript6');
const routes = appRoutePaths(readFileSync('frontend/src/App.tsx', 'utf8'), ts);
const modes = alchimieModeBindings(readFileSync('frontend/src/screens/Alchimie.tsx', 'utf8'), ts);
const ported = portedSetBindings('/work', routes);
const measured = measureProfile('/work/frontend/dist', JSON.parse(readFileSync('budgets.json')), routes, api);
console.log(JSON.stringify({ scope: 'Focused emitted current-route preflight; not unit/full acceptance', ported, modes, ...measured }, null, 2));
process.exitCode = measured.status === 'pass' ? 0 : 1;
JS
fi
python3 -I - "$out" <<'PY'
import hashlib, json, pathlib, sys
out = pathlib.Path(sys.argv[1])
commands = []
for label in ['typecheck', 'tools-typecheck', 'focused', 'scores', 'lint', 'build', 'docs', 'budgets']:
    exit_file = out / (label + '.exit')
    if not exit_file.exists():
        commands.append({'name': label, 'status': 'not-run', 'reason': 'build prerequisite failed'})
        continue
    row = {'name': label, 'exit_code': int(exit_file.read_text())}
    for stream in ['stdout', 'stderr']:
        p = out / (label + '.' + stream + '.log')
        b = p.read_bytes()
        row[stream] = {'path': p.name, 'bytes': len(b), 'sha256': hashlib.sha256(b).hexdigest()}
    commands.append(row)
record = {'schema': 1, 'scope': 'Focused preflight only; no canonical unit/full or milestone acceptance',
          'context': json.loads((out / 'context.json').read_text()), 'commands': commands}
(out / 'result.json').write_text(json.dumps(record, indent=2) + '\n')
print(json.dumps(record))
PY
exit "$failed"
