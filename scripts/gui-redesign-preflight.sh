#!/usr/bin/env bash
# Focused browser development through the owning pinned shell.
set -euo pipefail
[[ "$PWD" == /work && "$GATE_APP_URL" == http://localhost:8080 ]]
node --input-type=module - <<'JS'
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
const context = JSON.parse(readFileSync(".gate/wrapper-current.json"));
assert.equal(context.target, "shell");
assert.equal(context.sha, process.env.GATE_SHA);
assert.equal(context.tree_sha256, process.env.GATE_TREE_SHA256);
assert.ok(["agent:codex", "paul"].includes(context.operator));
JS
out=/work/.gate/shell/redesign
mkdir -p "$out"
cd /work/frontend
npm ci --no-audit --no-fund > "$out/npm-ci.log" 2>&1
cd /work

go -C go-backend build -o "$out/cat-browser-plan" ./cmd/cat-browser-plan
export CDR_BROWSER_PLAN_BINARY="$out/cat-browser-plan"

node scripts/gui-full-browser.mjs inventory > "$out/inventory.log" 2>&1
cp .gate/gen/browser-inventory.json "$out/browser-inventory.json"

node scripts/gui-style-audit.mjs --root /work > "$out/style-audit.json" || true
node -e 'const r=require(process.argv[1]); console.log("CSS bag audit", JSON.stringify(r.counters), JSON.stringify(r.findings))' "$out/style-audit.json"
if [[ "${1:-}" == inventory ]]; then exit 0; fi

cd /work/frontend
npm run build > "$out/current-build.log" 2>&1
projects=(--project desktop)
if [[ "${1:-}" == --all-projects || $# == 0 ]]; then
  projects=()
fi
if [[ "${1:-}" == --all-projects ]]; then shift; fi
node node_modules/@playwright/test/cli.js test --config playwright.gui.config.mjs   "${projects[@]}" --reporter json "$@" > "$out/playwright.json"
