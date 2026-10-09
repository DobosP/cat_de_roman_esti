import test from "node:test";
import assert from "node:assert/strict";
import * as fs from "node:fs";
import path from "node:path";
import { createHash } from "node:crypto";
import { fileURLToPath } from "node:url";
import { gzipSync } from "node:zlib";
import ts from "@typescript/typescript6";
import * as budget from "@roedu/web-kit/budget";
import { parserBinding } from "../scripts/compiler-runtime.mjs";
import { appRoutePaths, bindings, journeys, measureProfile, verifyTreeRows } from "../../scripts/gui-route-budgets.mjs";

// Synthetic asset attribution contracts only. These execute the installed public
// evaluator; they are not app/server/browser/device or legacy-runtime proof.
const repo = fileURLToPath(new URL("../../", import.meta.url)).replace(/\/$/, "");
const source = fs.readFileSync(new URL("../src/App.tsx", import.meta.url), "utf8");
const paths = ["/", "/alchimie", "/intrusul", "/perechi", "/cald-rece", "/lant", "/conexiuni", "/clasament"];
const account = "src/components/AccountBar.tsx";
const routeKeys = ["Alchimie", "Intrusul", "Perechi", "CaldRece", "Lant", "Conexiuni", "Ranking"].map((name) => `src/screens/${name}.tsx`);
const sha = (bytes) => createHash("sha256").update(bytes).digest("hex");
const budgetBytes = fs.readFileSync(new URL("../../budgets.json", import.meta.url));
const actualBudgets = JSON.parse(budgetBytes);

function write(root, name, data) {
  const file = path.join(root, name);
  fs.mkdirSync(path.dirname(file), { recursive: true });
  fs.writeFileSync(file, data);
}
function fixture(t) {
  assert.equal(process.platform, "linux");
  assert.equal(repo, "/work", "Actual owning runner required; no host test fallback");
  const current = JSON.parse(fs.readFileSync(path.join(repo, ".gate/wrapper-current.json")));
  assert.ok(["unit", "full", "shell"].includes(current.target));
  for (const [key, env] of [["sha", "GATE_SHA"], ["tree_sha256", "GATE_TREE_SHA256"], ["toolchain_digest", "TOOLCHAIN_DIGEST"]]) {
    assert.equal(current[key], process.env[env]);
  }
  assert.match(current.invocation, /^[a-f0-9]{8}-[a-f0-9]{4}-4[a-f0-9]{3}-[89ab][a-f0-9]{3}-[a-f0-9]{12}$/);
  let base = path.join(repo, ".gate");
  assert.equal(fs.realpathSync(base), base);
  assert.ok(fs.lstatSync(base).isDirectory() && !fs.lstatSync(base).isSymbolicLink());
  // Negative symlinks remain retained outside the target's receipt/artifact tree.
  for (const part of ["_temp", "gui-route-budget-synthetic", current.target, current.invocation]) {
    base = path.join(base, part);
    if (!fs.existsSync(base)) fs.mkdirSync(base, { mode: 0o700 });
    const info = fs.lstatSync(base);
    assert.equal(fs.realpathSync(base), base);
    assert.ok(info.isDirectory() && !info.isSymbolicLink()
      && (info.mode & 0o777) === 0o700 && info.uid === process.getuid(), "Private owned fixture ancestor required");
  }
  const root = fs.mkdtempSync(path.join(base, "NON-NATIVE-"));
  t.after(() => {
    // Retain every fixture, including failed/refused inputs. No snapshots or
    // candidate application; the parent captures the owning invocation.
    fs.writeFileSync(path.join(root, "scope.txt"), "Synthetic route-budget attribution only; no application/runtime qualification.\n");
  });
  const manifest = {
    "index.html": { file: "assets/entry.js", isEntry: true, imports: ["startup"], css: ["assets/global.css"] },
    startup: { file: "assets/startup.js", imports: ["shared"], dynamicImports: [account, ...routeKeys] },
    shared: { file: "assets/shared.js", imports: ["startup"], css: ["assets/shared.css"] },
    [account]: { file: "assets/account.js", isDynamicEntry: true, imports: ["account-deep", "shared"] },
    "account-deep": { file: "assets/account-deep.js", imports: ["shared"], css: ["assets/account.css"] },
  };
  for (const [index, key] of routeKeys.entries()) manifest[key] = {
    file: `assets/route-${index}.js`, isDynamicEntry: true, imports: ["shared"], css: [`assets/route-${index}.css`],
  };
  for (const entry of Object.values(manifest)) {
    write(root, entry.file, `/* ${entry.file} */\n` + "export const n = 42;\n".repeat(5));
    for (const css of entry.css ?? []) write(root, css, `/* ${css} */ .fixture{color:red}\n`);
  }
  write(root, ".vite/manifest.json", JSON.stringify(manifest));
  return { root, manifest };
}
function measured(f, budgets = actualBudgets) { return measureProfile(f.root, budgets, paths, budget); }

void test("actual JSX route paths and source module identities cover every default route plus both Alchimie journeys", () => {
  parserBinding(path.join(repo, "frontend"), ts);
  assert.deepEqual(appRoutePaths(source, ts), paths);
  assert.equal(journeys.length, 10);
  for (const name of ["/alchimie", "/alchimie?mode=challenges", "/alchimie?mode=explore"]) assert.ok(journeys.includes(name));
  for (const mutation of [
    source.replace('path="/lant"', 'path="/unknown"'),
    source.replace('path="/lant"', 'path="/perechi"'),
    source.replace('import("./screens/Lant")', 'import("./screens/Ranking")'),
    source.replace('<Lant onExit={goHome} onToast={pushToast} />', '<Ranking />'),
    source.replace('to="/" replace', 'to="/unmeasured" replace'),
  ]) {
    assert.notEqual(mutation, source, "The authored source mutation must affect its actual input");
    assert.throws(() => appRoutePaths(mutation, ts), "An unbound/mismatched route cannot silently disappear");
  }
});

void test("public evaluator follows genuine static owners, mandatory deep AccountBar dependencies and shared cycles exactly once", (t) => {
  const f = fixture(t), result = measured(f);
  assert.equal(result.report.routes.length, 10);
  assert.deepEqual(result.report.routes.map((item) => item.name).sort(), [...journeys].sort());
  const home = result.report.routes.find((item) => item.name === "/");
  assert.deepEqual(home.js.files, ["assets/account-deep.js", "assets/account.js", "assets/entry.js", "assets/shared.js", "assets/startup.js"]);
  assert.ok(home.css.files.includes("assets/account.css"));
  assert.equal(home.js.files.filter((file) => file === "assets/shared.js").length, 1);
  for (const [index, route] of ["/alchimie", "/intrusul", "/perechi", "/cald-rece", "/lant", "/conexiuni", "/clasament"].entries()) {
    const item = result.report.routes.find((row) => row.name === route);
    assert.ok(item.js.files.includes(`assets/route-${index}.js`));
    assert.ok(item.js.files.includes("assets/account-deep.js"));
    assert.equal(item.js.files.filter((file) => file.startsWith("assets/route-")).length, 1);
  }
  assert.equal(result.report.global_css.status, "recorded");
  assert.equal(result.report.global_css.limit_gz, null);
  assert.deepEqual(result.report.unmeasured_metrics, ["lcp_ms", "inp_ms"]);
});

void test("missing required source roots, malformed references and incomplete route lists refuse attribution", (t) => {
  const f = fixture(t);
  for (const mutate of [
    (m) => { delete m[account]; },
    (m) => { delete m[routeKeys[6]]; },
    (m) => { m.startup.dynamicImports = m.startup.dynamicImports.filter((key) => key !== account); },
    (m) => { m[account].imports.push("absent"); },
    (m) => { m[account].imports = "shared"; },
    (m) => { m[routeKeys[0]].isDynamicEntry = false; },
    (m) => { m.hidden = { file: "assets/other.js", isEntry: true }; },
  ]) {
    const changed = structuredClone(f.manifest); mutate(changed);
    assert.throws(() => bindings(changed, paths));
  }
  assert.throws(() => bindings(f.manifest, paths.slice(0, -1)));
  fs.unlinkSync(path.join(f.root, "assets/account-deep.js"));
  assert.throws(() => measured(f), "Missing mandatory bytes cannot become zero-size measured pass");
});

void test("actual public budget status stays red with complete nonempty measurements and unchanged literal limits", (t) => {
  const f = fixture(t), green = measured(f);
  assert.equal(green.report.status, "pass");
  const budgets = structuredClone(actualBudgets);
  budgets.js["cat-initial"].limit_gz = 0; // explicitly synthetic refusal threshold, never written to owning budgets
  const red = measured(f, budgets);
  assert.equal(red.report.status, "fail");
  assert.equal(red.report.routes.length, 10);
  assert.ok(red.report.routes.every((item) => item.js.status === "fail" && item.js.actual_gz > 0 && item.js.files.length >= 5));
  assert.ok(Object.values(red.budgets).some((item) => item.status === "fail" && item.actual > item.limit));
  assert.equal(actualBudgets.js["cat-initial"].limit_gz, 40960);
  assert.equal(actualBudgets.js["cat-initial"].target_gz, 30720);
  assert.deepEqual(fs.readFileSync(new URL("../../budgets.json", import.meta.url)), budgetBytes);
});

void test("verified gzip bytes and separately bound active/frozen profiles remain distinct; stale sidecars refuse", (t) => {
  const active = fixture(t), frozen = fixture(t);
  const first = measured(active);
  const bytes = Buffer.from(Array.from({ length: 4096 }, (_, index) => (index * 73 + (index >> 4)) % 256));
  write(frozen.root, "assets/account-deep.js", bytes);
  const compressed = gzipSync(bytes, { level: 9 });
  write(frozen.root, "assets/account-deep.js.gz", compressed);
  const second = measured(frozen);
  assert.notEqual(second.report.routes.find((item) => item.name === "/").js.actual_gz,
    first.report.routes.find((item) => item.name === "/").js.actual_gz);
  assert.equal(second.report.routes.find((item) => item.name === "/").js.actual_gz
    - first.report.routes.find((item) => item.name === "/").js.actual_gz,
  compressed.length - gzipSync(fs.readFileSync(path.join(active.root, "assets/account-deep.js")), { level: 6 }).length);
  const changed = Buffer.from(bytes);
  changed[0] ^= 0xff;
  assert.equal(changed.length, bytes.length);
  assert.notDeepEqual(changed, bytes);
  write(frozen.root, "assets/account-deep.js", changed);
  assert.throws(() => measured(frozen), /stale gzip/);
});

void test("complete asset ledgers refuse omitted, extra, changed and symlinked files instead of trusting selected sums", (t) => {
  const f = fixture(t);
  write(f.root, "bound/a.js", "one"); write(f.root, "bound/b.css", "two");
  const rows = ["a.js", "b.css"].map((name) => {
    const bytes = fs.readFileSync(path.join(f.root, "bound", name));
    return { path: name, bytes: bytes.length, sha256: sha(bytes) };
  });
  assert.deepEqual(verifyTreeRows(f.root, "bound", rows), rows);
  assert.throws(() => verifyTreeRows(f.root, "bound", rows.slice(0, 1)));
  assert.throws(() => verifyTreeRows(f.root, "bound", [...rows, rows[0]]));
  write(f.root, "bound/a.js", "changed");
  assert.throws(() => verifyTreeRows(f.root, "bound", rows));
  write(f.root, "bound/a.js", "one");
  fs.symlinkSync("a.js", path.join(f.root, "bound/alias.js"));
  assert.throws(() => verifyTreeRows(f.root, "bound", rows), /symlink/);
});
