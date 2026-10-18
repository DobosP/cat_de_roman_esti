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
import { appRoutePaths, alchimieModeBindings, alchimieModeScreens, bindings, classifyProfiles, frozenBaselineReferences, journeys, measureProfile, portedPaths, portedJourneys, portedSetBindings, verifyFrozenBaseline, verifyTreeRows } from "../../scripts/gui-route-budgets.mjs";
import { readTarGz } from "../../tools/gui-bootstrap-webkit/scripts/kit-sync.mjs";

// Synthetic asset attribution contracts only. These execute the installed public
// evaluator; they are not app/server/browser/device or legacy-runtime proof.
const repo = fileURLToPath(new URL("../../", import.meta.url)).replace(/\/$/, "");
const source = fs.readFileSync(new URL("../src/App.tsx", import.meta.url), "utf8");
// The current (Preact) bundle carries the ported set; the frozen legacy bundle every original route (ADR-0197).
const paths = ["/", "/intrusul", "/perechi", "/conexiuni", "/alchimie", "/cald-rece", "/lant", "/clasament"];
const frozenPaths = ["/", "/alchimie", "/intrusul", "/perechi", "/cald-rece", "/lant", "/conexiuni", "/clasament"];
const account = "src/components/AccountBar.tsx";
const screenKeys = { active: ["Intrusul", "Perechi", "Conexiuni", "Alchimie", "CaldRece", "Lant", "Ranking", "Home"], "frozen-legacy": ["Alchimie", "Intrusul", "Perechi", "CaldRece", "Lant", "Conexiuni", "Ranking"] };
const routeKeys = screenKeys.active.map((name) => `src/screens/${name}.tsx`);
const sha = (bytes) => createHash("sha256").update(bytes).digest("hex");
const budgetBytes = fs.readFileSync(new URL("../../budgets.json", import.meta.url));
const actualBudgets = JSON.parse(budgetBytes);

function write(root, name, data) {
  const file = path.join(root, name);
  fs.mkdirSync(path.dirname(file), { recursive: true });
  fs.writeFileSync(file, data);
}
function fixture(t, profile = "active") {
  const keys = screenKeys[profile].map((name) => `src/screens/${name}.tsx`);
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
    startup: { file: "assets/startup.js", imports: ["shared"], dynamicImports: [account, ...keys] },
    shared: { file: "assets/shared.js", imports: ["startup"], css: ["assets/shared.css"] },
    [account]: { file: "assets/account.js", isDynamicEntry: true, imports: ["account-deep", "shared"] },
    "account-deep": { file: "assets/account-deep.js", imports: ["shared"], css: ["assets/account.css"] },
  };
  for (const [index, key] of keys.entries()) manifest[key] = {
    file: `assets/route-${index}.js`, isDynamicEntry: true, imports: ["shared"], css: [`assets/route-${index}.css`],
  };
  if (profile === "active") {
    manifest["src/screens/Home.tsx"].imports.push("home-deep");
    manifest["home-deep"] = { file: "assets/home-deep.js", imports: ["shared"], css: ["assets/home-deep.css"] };
    manifest["src/screens/Alchimie.tsx"].dynamicImports = Object.values(alchimieModeScreens);
    for (const [mode, key] of Object.entries(alchimieModeScreens)) manifest[key] = { file: `assets/alchimie-${mode}.js`, isDynamicEntry: true, imports: ["shared"], css: [`assets/alchimie-${mode}.css`] };
  }
  for (const entry of Object.values(manifest)) {
    write(root, entry.file, `/* ${entry.file} */\n` + "export const n = 42;\n".repeat(5));
    for (const css of entry.css ?? []) write(root, css, `/* ${css} */ .fixture{color:red}\n`);
  }
  write(root, ".vite/manifest.json", JSON.stringify(manifest));
  return { root, manifest };
}
function measured(f, budgets = actualBudgets, profile = "active") {
  return measureProfile(f.root, budgets, profile === "active" ? paths : frozenPaths, budget, profile);
}

void test("Alchimie source binds two literal lazy leaves to the captured frame URL", () => {
  const selector = fs.readFileSync(new URL("../src/screens/Alchimie.tsx", import.meta.url), "utf8");
  const actual = alchimieModeBindings(selector, ts);
  assert.deepEqual(actual.modes, alchimieModeScreens); assert.equal(actual.saved_default, "challenges");
  for (const changed of [
    selector.replace('import("./AlchimieExplore")', 'import("./AlchimieChallenge")'),
    selector.replace('alchimieMode(url, legacyResume)', 'alchimieMode(location.href, legacyResume)'),
    selector.replace('? <AlchimieChallenge', '? <AlchimieExplore'),
    'import Eager from "./AlchimieExplore";\n' + selector,
  ]) { assert.notEqual(changed, selector); assert.throws(() => alchimieModeBindings(changed, ts)); }
});
void test("Alchimie mode rows charge the selected leaf and refuse missing or eager mode boundaries", (t) => {
  const f = fixture(t), report = measured(f).report;
  const current = report.routes.find((item) => item.name === "/alchimie");
  const explore = report.routes.find((item) => item.name === "/alchimie?mode=explore");
  const challenge = report.routes.find((item) => item.name === "/alchimie?mode=challenges");
  assert.deepEqual(current.js.files, explore.js.files);
  for (const [row, own, other] of [[explore, "explore", "challenges"], [challenge, "challenges", "explore"]]) {
    assert.ok(row.js.files.includes(`assets/alchimie-${own}.js`));
    assert.ok(!row.js.files.includes(`assets/alchimie-${other}.js`));
    assert.ok(row.js.files.includes("assets/route-3.js") && row.js.files.includes("assets/account-deep.js"));
    assert.equal(row.js.limit_gz, 40960);
  }
  for (const mutate of [
    (m) => { delete m[alchimieModeScreens.explore]; },
    (m) => { m["src/screens/Alchimie.tsx"].dynamicImports.pop(); },
    (m) => { m["src/screens/Alchimie.tsx"].imports.push(alchimieModeScreens.challenges); },
    (m) => { m[alchimieModeScreens.explore].imports.push(alchimieModeScreens.challenges); },
  ]) { const changed = structuredClone(f.manifest); mutate(changed); assert.throws(() => bindings(changed, paths)); }
});

void test("the literal route switch, the client table and the Go set agree on all eight current paths", () => {
  parserBinding(path.join(repo, "frontend"), ts);
  assert.deepEqual(appRoutePaths(source, ts), paths);
  assert.deepEqual([...portedPaths], paths);
  assert.deepEqual([...portedJourneys], [...paths, "/alchimie?mode=challenges", "/alchimie?mode=explore"]);
  assert.equal(journeys.length, 10);
  for (const name of ["/alchimie", "/alchimie?mode=challenges", "/alchimie?mode=explore"]) assert.ok(journeys.includes(name));
  const bound = portedSetBindings(repo, paths);
  assert.deepEqual(bound.ported, paths);
  assert.deepEqual(bound.frozen_legacy, []);
  assert.throws(() => portedSetBindings(repo, [...paths, "/lant"]), /ported set differs/);
  assert.throws(() => portedSetBindings(repo, paths.slice(0, -1)), /ported set differs/);
  for (const mutation of [
    source.replace('case "/intrusul":', 'case "/unknown":'),
    source.replace('case "/intrusul":', 'case "/conexiuni":'),
    source.replace('import("./screens/Intrusul")', 'import("./screens/Ranking")'),
    source.replace('const Home = lazyScreen(() => import("./screens/Home"));', 'import Home from "./screens/Home";'),
    source.replace('<Intrusul onExit={goHome} onToast={pushToast} />', '<Conexiuni onExit={goHome} onToast={pushToast} />'),
    source.replace('screen = <FallbackRoute url={url} />;', 'screen = <Home onToast={pushToast} />;'),
    source.replace('portedPath(path) ? path : "fallback"', 'path'),
  ]) {
    assert.notEqual(mutation, source, "The authored source mutation must affect its actual input");
    assert.throws(() => appRoutePaths(mutation, ts), "An unbound/mismatched route cannot silently disappear");
  }
});

void test("public evaluator follows genuine static owners, mandatory deep AccountBar dependencies and shared cycles exactly once", (t) => {
  const f = fixture(t), result = measured(f);
  assert.equal(result.report.routes.length, 10);
  assert.deepEqual(result.report.routes.map((item) => item.name).sort(), [...portedJourneys].sort());
  const home = result.report.routes.find((item) => item.name === "/");
  assert.deepEqual(home.js.files, ["assets/account-deep.js", "assets/account.js", "assets/entry.js", "assets/home-deep.js", "assets/route-7.js", "assets/shared.js", "assets/startup.js"]);
  assert.ok(home.css.files.includes("assets/account.css"));
  assert.ok(home.css.files.includes("assets/home-deep.css"));
  assert.equal(home.js.files.filter((file) => file === "assets/shared.js").length, 1);
  for (const [index, route] of ["/intrusul", "/perechi", "/conexiuni"].entries()) {
    const item = result.report.routes.find((row) => row.name === route);
    assert.ok(item.js.files.includes(`assets/route-${index}.js`));
    assert.ok(item.js.files.includes("assets/account-deep.js"));
    assert.equal(item.js.files.filter((file) => file.startsWith("assets/route-")).length, 1);
    assert.ok(!item.js.files.includes("assets/route-7.js") && !item.js.files.includes("assets/home-deep.js"));
  }
  assert.equal(result.report.global_css.status, "recorded");
  assert.equal(result.report.global_css.limit_gz, null);
  assert.deepEqual(result.report.unmeasured_metrics, ["lcp_ms", "inp_ms"]);
  const frozen = fixture(t, "frozen-legacy"), legacy = measured(frozen, actualBudgets, "frozen-legacy");
  assert.equal(legacy.report.routes.length, 10);
  assert.deepEqual(legacy.report.routes.map((item) => item.name).sort(), [...journeys].sort());
  assert.throws(() => measureProfile(f.root, actualBudgets, [...paths, "/unknown"], budget, "active"), "The active profile cannot claim an unknown route");
  assert.throws(() => measureProfile(frozen.root, actualBudgets, paths.slice(1), budget, "frozen-legacy"), "The frozen profile must keep every original journey");
});

void test("Home attribution refuses missing selected dependencies or an eagerly shared Home leaf", (t) => {
  const f = fixture(t), home = "src/screens/Home.tsx";
  assert.deepEqual(bindings(f.manifest, paths).config.routes["/"].entries, ["index.html", account, home]);
  for (const mutate of [
    (m) => { delete m[home]; },
    (m) => { delete m["home-deep"]; },
    (m) => { m[home].isDynamicEntry = false; },
    (m) => { m.startup.imports.push(home); },
    (m) => { m[account].imports.push(home); },
    (m) => { m[alchimieModeScreens.challenges].imports.push(home); },
  ]) { const changed = structuredClone(f.manifest); mutate(changed); assert.throws(() => bindings(changed, paths)); }
});

void test("missing required source roots, malformed references and incomplete route lists refuse attribution", (t) => {
  const f = fixture(t);
  for (const mutate of [
    (m) => { delete m[account]; },
    (m) => { delete m[routeKeys[1]]; },
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

// Copies only the actual immutable frozen archive/source receipts into an owned
// synthetic transport fixture. This does not fabricate a current sync/runtime.
function frozenFixture(t) {
  const f = fixture(t);
  for (const name of frozenBaselineReferences) write(f.root, name, fs.readFileSync(path.join(repo, name)));
  const proof = JSON.parse(fs.readFileSync(path.join(f.root, "legacy/original-bundle.json")));
  for (const name of [proof.archive, proof.archive + ".sha256"]) write(f.root, name, fs.readFileSync(path.join(repo, name)));
  for (const [name, entry] of readTarGz(fs.readFileSync(path.join(f.root, proof.archive)))) {
    assert.equal(entry.type, "file");
    write(f.root, "go-backend/embedfs/legacy/" + name, entry.data);
  }
  return { ...f, proof, sync: { legacy_sha256: proof.sha256, legacy: proof.files } };
}
function verifiedFrozen(f) { return verifyFrozenBaseline(f.root, f.sync, readTarGz); }
function frozenMeasured(f) { return measureProfile(path.join(f.root, "go-backend/embedfs/legacy"), actualBudgets, frozenPaths, budget, "frozen-legacy"); }

void test("owner policy records every frozen SDK failure while compliant active budgets and exact original integrity qualify", (t) => {
  const active = fixture(t), frozen = frozenFixture(t), integrity = verifiedFrozen(frozen);
  const profiles = { active: measured(active), "frozen-legacy": frozenMeasured(frozen) };
  assert.equal(profiles.active.report.status, "pass");
  assert.equal(profiles["frozen-legacy"].report.status, "fail");
  assert.equal(profiles["frozen-legacy"].report.routes.length, 10);
  assert.ok(profiles["frozen-legacy"].report.routes.every((item) => item.js.status === "fail" && item.js.limit_gz === 40960));
  assert.equal(profiles.active.report.routes.length, 10);
  const before = JSON.stringify(profiles), result = classifyProfiles(profiles, integrity, "unit");
  assert.equal(result.status, "pass");
  assert.equal(JSON.stringify(profiles), before, "Raw SDK reports/statuses cannot be rewritten");
  assert.deepEqual(result.ported_routes, paths);
  assert.deepEqual(Object.keys(result.gate_budgets).filter((name) => name.startsWith("gate:active:route-js:")).sort(), portedJourneys.map((name) => `gate:active:route-js:${name}`).sort());
  for (const name of journeys) assert.equal(result.delivery[name], paths.includes(name.split("?")[0]) ? "current" : "frozen-legacy");
  assert.equal(result.frozen_legacy_routes.length, 0);
  for (const name of journeys) {
    assert.ok(Object.hasOwn(result.gate_budgets, `gate:active:route-js:${name}`), "Every M3 journey must earn an active numeric gate row");
    assert.equal(result.budgets[`baseline:frozen-legacy:route-js:${name}`].status, "recorded");
  }
  assert.equal(Object.keys(result.budgets).length, Object.keys(profiles.active.budgets).length + Object.keys(profiles["frozen-legacy"].budgets).length);
  for (const [name, value] of Object.entries(profiles["frozen-legacy"].budgets)) {
    const recorded = result.budgets["baseline:frozen-legacy:" + name];
    assert.equal(recorded.classification, "frozen-baseline-measurement");
    assert.equal(recorded.sdk_status, value.status);
    assert.equal(recorded.actual, value.actual); assert.equal(recorded.limit, value.limit);
    assert.equal(recorded.status, "recorded");
    assert.equal(recorded.raw_report, ".gate/unit/route-budgets/frozen-legacy.json");
    assert.equal(recorded.integrity_check, "cat-frozen-legacy-integrity");
  }
  assert.deepEqual(integrity.required_full_runtime_checks, ["cat-legacy-owner-journey", "cat-browser-full"]);
});

void test("owner policy cannot qualify over-limit active bytes and retains unchanged active40960 target30720", (t) => {
  const active = fixture(t), frozen = frozenFixture(t);
  let seed = 0x1372ac91;
  const bytes = Buffer.from(Array.from({ length: 65536 }, () => {
    seed ^= seed << 13; seed ^= seed >>> 17; seed ^= seed << 5;
    return seed & 255;
  }));
  write(active.root, "assets/entry.js", bytes); // Synthetic attribution bytes, never executed as a program.
  const profiles = { active: measured(active), "frozen-legacy": frozenMeasured(frozen) };
  assert.equal(profiles.active.report.status, "fail");
  assert.ok(profiles.active.report.routes.every((item) => item.js.actual_gz > 40960 && item.js.status === "fail"));
  const result = classifyProfiles(profiles, verifiedFrozen(frozen), "full");
  assert.equal(result.status, "fail");
  assert.ok(Object.entries(result.budgets).filter(([name]) => name.startsWith("gate:active:route-js:")).every(([, item]) => item.status === "fail" && item.sdk_status === "fail" && item.classification === "active-numeric-gate"));
  assert.equal(actualBudgets.js["cat-initial"].limit_gz, 40960);
  assert.equal(actualBudgets.js["cat-initial"].target_gz, 30720);
  assert.deepEqual(fs.readFileSync(new URL("../../budgets.json", import.meta.url)), budgetBytes);
});

void test("frozen baseline refuses changed producer source receipt stdout proof archive and manifest identities", (t) => {
  const f = frozenFixture(t);
  verifiedFrozen(f);
  for (const name of [...frozenBaselineReferences, f.proof.archive, f.proof.archive + ".sha256", "go-backend/embedfs/legacy/.vite/manifest.json"]) {
    const file = path.join(f.root, name), original = fs.readFileSync(file), changed = Buffer.from(original);
    changed[0] ^= 1;
    write(f.root, name, changed);
    assert.throws(() => verifiedFrozen(f), "Any original source/receipt/archive/manifest byte change must fail");
    write(f.root, name, original);
    verifiedFrozen(f);
  }
  const proof = structuredClone(f.proof);
  proof.sha = "0".repeat(40);
  write(f.root, "legacy/original-bundle.json", JSON.stringify(proof));
  assert.throws(() => verifiedFrozen(f), /Original producer proof identity/);
});

void test("frozen baseline refuses missing extra aliased or changed asset bytes and mismatched sync without dropping roots", (t) => {
  const f = frozenFixture(t), owner = f.proof.files.find((item) => item.path.endsWith(".woff2"));
  const name = "go-backend/embedfs/legacy/" + owner.path, file = path.join(f.root, name), original = fs.readFileSync(file);
  verifiedFrozen(f);
  fs.unlinkSync(file); assert.throws(() => verifiedFrozen(f)); write(f.root, name, original);
  write(f.root, name, Buffer.from("changed")); assert.throws(() => verifiedFrozen(f)); write(f.root, name, original);
  const extra = path.join(f.root, "go-backend/embedfs/legacy/extra.js");
  write(f.root, "go-backend/embedfs/legacy/extra.js", "extra"); assert.throws(() => verifiedFrozen(f)); fs.unlinkSync(extra);
  fs.unlinkSync(file); fs.symlinkSync(path.basename(owner.path), file);
  assert.throws(() => verifiedFrozen(f), /symlink/); fs.unlinkSync(file); write(f.root, name, original);
  verifiedFrozen(f);
  const sync = structuredClone(f.sync); sync.legacy[0].sha256 = "0".repeat(64);
  assert.throws(() => verifyFrozenBaseline(f.root, sync, readTarGz));
  const profiles = { active: measured(f), "frozen-legacy": frozenMeasured(f) };
  const missing = structuredClone(profiles); missing["frozen-legacy"].report.routes.pop();
  assert.throws(() => classifyProfiles(missing, verifiedFrozen(f), "unit"));
});

void test("budget classification refuses missing or relabeled frozen integrity and unexpected profiles", (t) => {
  const f = frozenFixture(t), integrity = verifiedFrozen(f);
  const profiles = { active: measured(f), "frozen-legacy": frozenMeasured(f) };
  assert.throws(() => classifyProfiles(profiles, null, "unit"));
  for (const key of ["status", "source", "manifest_sha256", "proof_sha256", "result_sha256", "archive_sha256"]) {
    const changed = structuredClone(integrity); changed[key] = "changed";
    assert.throws(() => classifyProfiles(profiles, changed, "unit"));
  }
  assert.throws(() => classifyProfiles({ active: profiles.active }, integrity, "unit"));
  assert.throws(() => classifyProfiles(profiles, integrity, "shell"));
});

void test("installed public gate-result contract rejects the mixed baseline table and validates only active numeric projection", async (t) => {
  const f = frozenFixture(t), profiles = { active: measured(f), "frozen-legacy": frozenMeasured(f) };
  const before = JSON.stringify(profiles), result = classifyProfiles(profiles, verifiedFrozen(f), "unit");
  // Resolve the shipped validator next to the actual installed public budget
  // entry. No copied validator, pinned-package edit or synthetic receipt is used.
  const validatorURL = new URL("../schemas/validate.mjs", import.meta.resolve("@roedu/web-kit/budget"));
  const validatorPath = fileURLToPath(validatorURL);
  assert.equal(validatorPath, path.join(repo, "frontend/node_modules/@roedu/web-kit/schemas/validate.mjs"));
  assert.equal(fs.realpathSync(validatorPath), validatorPath);
  assert.ok(fs.lstatSync(validatorPath).isFile() && !fs.lstatSync(validatorPath).isSymbolicLink());
  const { assertGateResult, validate } = await import(validatorURL.href);
  const schema = JSON.parse(fs.readFileSync(new URL("./result.schema.json", validatorURL)));
  // In-memory protocol fixture only. It is never written as an actual gate
  // receipt and carries no application, source/image or runtime qualification.
  const synthetic = (budgets) => ({ schema: 1, target: "unit", status: "pass",
    sha: "1".repeat(40), dirty: false, tree_sha256: "2".repeat(64),
    toolchain_digest: "sha256:" + "3".repeat(64), versions_lock_sha256: "4".repeat(64), parallel: 1,
    started: "2026-10-11T00:00:00.000Z", finished: "2026-10-11T00:00:01.000Z",
    checks: [{ name: "synthetic-active-numeric", status: "pass", duration_ms: 0 },
      { name: "cat-frozen-legacy-integrity", status: "pass", duration_ms: 0 }],
    csp: { stage: "enforced", violations: 0, legacy_violations: 0 }, budgets, artifacts: [] });
  validate(schema, synthetic(result.budgets));
  assert.throws(() => assertGateResult(synthetic(result.budgets)), /budget status must reflect measured actual/);
  assert.equal(Object.keys(result.gate_budgets).length, Object.keys(profiles.active.budgets).length);
  assert.ok(Object.keys(result.gate_budgets).every((name) => name.startsWith("gate:active:")));
  for (const [name, value] of Object.entries(result.gate_budgets)) assert.deepEqual(value, result.budgets[name]);
  validate(schema, synthetic(result.gate_budgets));
  assert.doesNotThrow(() => assertGateResult(synthetic(result.gate_budgets)));
  const over = structuredClone(result.gate_budgets);
  const key = Object.keys(over).find((name) => name.startsWith("gate:active:route-js:"));
  assert.ok(key);
  over[key].actual = over[key].limit + 1; over[key].status = "fail"; over[key].sdk_status = "fail";
  assert.throws(() => assertGateResult(synthetic(over)), /failed budget cannot pass/);
  assert.equal(JSON.stringify(profiles), before);
  assert.equal(profiles["frozen-legacy"].report.routes.length, 10);
  assert.ok(profiles["frozen-legacy"].report.routes.every((item) => item.js.status === "fail" && item.js.limit_gz === 40960));
  assert.ok(Object.entries(result.budgets).filter(([name]) => name.startsWith("baseline:frozen-legacy:route-js:")).every(([, value]) => value.status === "recorded" && value.sdk_status === "fail"));
  assert.equal(actualBudgets.js["cat-initial"].limit_gz, 40960);
  assert.equal(actualBudgets.js["cat-initial"].target_gz, 30720);
});
