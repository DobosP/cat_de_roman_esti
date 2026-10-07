import * as fs from "node:fs";
import path from "node:path";
import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import { spawnSync } from "node:child_process";
import { pathToFileURL } from "node:url";

const hash = (data) => createHash("sha256").update(data).digest("hex");
const configured = spawnSync("task", ["--silent", "repo:kit-config"], { encoding: "utf8" });
assert.equal(configured.status, 0);
const config = JSON.parse(configured.stdout);
const { evaluate } = await import(pathToFileURL(path.resolve(config.npm_dir, "budget/index.mjs")).href);
const assets = "cat_de_roman_esti/web/static", manifestBytes = fs.readFileSync(`${assets}/.vite/manifest.json`);
const budgetsBytes = fs.readFileSync("budgets.json"), manifest = JSON.parse(manifestBytes);
// Root is a real Go-served SPA page and the original App's Home route. A single
// genuine entry closure is sufficient to expose the current budget boundary;
// this is not a substituted production route-registration inventory.
assert.equal(manifest["index.html"].isEntry, true);
const report = evaluate(JSON.parse(budgetsBytes), manifest, [{ name: "home", path: "/", template: "SPA" }], {
  schema: 1, routes: { home: { class: "cat-initial", entries: ["index.html"] } },
  global_css: manifest["index.html"].css || [], vendors: {},
}, assets);
assert.equal(report.status, "fail");
assert.ok(report.routes[0].js.actual_gz > report.routes[0].js.limit_gz);
const output = { schema: 1, check: "cat-original-budget-boundary", scope: "actual-original-home-entry-counterexample", sha: process.env.GATE_SHA, tree_sha256: process.env.GATE_TREE_SHA256, toolchain_digest: process.env.TOOLCHAIN_DIGEST, manifest_sha256: hash(manifestBytes), budgets_sha256: hash(budgetsBytes), report };
fs.mkdirSync(".gate/gen/original", { recursive: true });
fs.writeFileSync(".gate/gen/original/budget-boundary.json", JSON.stringify(output, null, 2) + "\n");
process.stdout.write(JSON.stringify(output, null, 2) + "\n");
