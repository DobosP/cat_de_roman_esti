import assert from "node:assert/strict";
import * as fs from "node:fs";
import path from "node:path";
import { createHash } from "node:crypto";
import { fileURLToPath, pathToFileURL } from "node:url";
import { collectInitialBundleFiles } from "../frontend/scripts/check-bundle-budget.mjs";
import { parserBinding } from "../frontend/scripts/compiler-runtime.mjs";
import { resolveHookRuntime } from "./gui-hook-runtime.mjs";

const hash = (bytes) => createHash("sha256").update(bytes).digest("hex");
const legacyHash = "742bb11130fa2bf52ba5c64cb9cfd452f7d8ac3a4fd9dc6d77e8064a6b8fef65";
const account = "src/components/AccountBar.tsx";
const screens = Object.freeze({
  "/": null,
  "/alchimie": "src/screens/Alchimie.tsx",
  "/intrusul": "src/screens/Intrusul.tsx",
  "/perechi": "src/screens/Perechi.tsx",
  "/cald-rece": "src/screens/CaldRece.tsx",
  "/lant": "src/screens/Lant.tsx",
  "/conexiuni": "src/screens/Conexiuni.tsx",
  "/clasament": "src/screens/Ranking.tsx",
});
const components = { "/": "Home", "/alchimie": "Alchimie", "/intrusul": "Intrusul",
  "/perechi": "Perechi", "/cald-rece": "CaldRece", "/lant": "Lant",
  "/conexiuni": "Conexiuni", "/clasament": "Ranking" };
// The default /alchimie route is measured too. The two existing baseline
// journeys select different views from its same actual static module closure.
export const journeys = Object.freeze([...Object.keys(screens),
  "/alchimie?mode=challenges", "/alchimie?mode=explore"]);

function relative(value) {
  assert.ok(typeof value === "string" && value && !path.isAbsolute(value)
    && !/[\\:\x00-\x1f\x7f]/.test(value)
    && value.split("/").every((part) => part && part !== "." && part !== ".."), "Literal confined path required");
  return value;
}
function regular(root, name) {
  let cursor = root;
  for (const [index, part] of relative(name).split("/").entries()) {
    cursor = path.join(cursor, part);
    const info = fs.lstatSync(cursor);
    assert.ok(!info.isSymbolicLink() && (index === name.split("/").length - 1
      ? info.isFile() : info.isDirectory()), "Regular source/asset path required");
  }
  assert.equal(fs.realpathSync(cursor), cursor, "Source/asset alias refused");
  return cursor;
}
function read(root, name) { return fs.readFileSync(regular(root, name)); }
function json(root, name) { return JSON.parse(read(root, name)); }
function row(root, name) {
  const bytes = read(root, name);
  return { path: name, bytes: bytes.length, sha256: hash(bytes) };
}

/** Discover real JSX Route paths, not source substrings or chunk-name guesses. */
export function appRoutePaths(source, ts) {
  const file = ts.createSourceFile("App.tsx", source, ts.ScriptTarget.Latest, true, ts.ScriptKind.TSX);
  assert.equal(file.parseDiagnostics.length, 0, "Current App route source must parse");
  const paths = [];
  const modules = new Map();
  function imports(node) {
    if (ts.isImportDeclaration(node) && ts.isStringLiteral(node.moduleSpecifier)
      && node.importClause?.name) modules.set(node.importClause.name.text, node.moduleSpecifier.text);
    if (ts.isVariableDeclaration(node) && ts.isIdentifier(node.name) && node.initializer
      && ts.isCallExpression(node.initializer) && node.initializer.expression.getText(file) === "lazy") {
      const found = [];
      function dynamic(child) {
        if (ts.isCallExpression(child) && child.expression.kind === ts.SyntaxKind.ImportKeyword) {
          assert.ok(child.arguments.length === 1 && ts.isStringLiteral(child.arguments[0]), "Literal lazy import required");
          found.push(child.arguments[0].text);
        }
        ts.forEachChild(child, dynamic);
      }
      dynamic(node.initializer);
      assert.equal(found.length, 1, "One actual source module per lazy route component required");
      modules.set(node.name.text, found[0]);
    }
    ts.forEachChild(node, imports);
  }
  imports(file);
  assert.equal(modules.get("AccountBar"), "./components/AccountBar", "Mandatory root must bind its actual module");
  for (const [route, component] of Object.entries(components)) {
    const expected = screens[route] ?? "src/screens/Home.tsx";
    assert.equal(modules.get(component), "./" + expected.slice(4, -4), "Route component must bind its real source module");
  }
  let redirect = 0;
  function visit(node) {
    if ((ts.isJsxOpeningElement(node) || ts.isJsxSelfClosingElement(node))
      && ts.isIdentifier(node.tagName) && node.tagName.text === "Route") {
      const attributes = node.attributes.properties;
      assert.ok(attributes.every(ts.isJsxAttribute), "Route spreads need explicit budget attribution");
      const declared = attributes.filter((item) => item.name.getText(file) === "path");
      assert.equal(declared.length, 1, "Each actual Route needs one literal path");
      assert.ok(declared[0].initializer && ts.isStringLiteral(declared[0].initializer), "Nonliteral Route path refused");
      const value = declared[0].initializer.text;
      if (value === "*") {
        const element = attributes.find((item) => item.name.getText(file) === "element")?.initializer;
        assert.ok(element && ts.isJsxExpression(element) && element.expression
          && ts.isJsxSelfClosingElement(element.expression)
          && element.expression.tagName.getText(file) === "Navigate", "Only the existing home redirect is unmeasured");
        const to = element.expression.attributes.properties.find((item) => ts.isJsxAttribute(item) && item.name.getText(file) === "to");
        assert.ok(to?.initializer && ts.isStringLiteral(to.initializer) && to.initializer.text === "/", "Wildcard must redirect to measured home");
        redirect++;
      } else {
        assert.ok(Object.hasOwn(components, value), "Unbound actual SPA route refused");
        const element = attributes.find((item) => item.name.getText(file) === "element")?.initializer;
        assert.ok(element && ts.isJsxExpression(element) && element.expression, "Actual route element required");
        let matches = 0;
        function component(child) {
          if ((ts.isJsxOpeningElement(child) || ts.isJsxSelfClosingElement(child))
            && child.tagName.getText(file) === components[value]) matches++;
          ts.forEachChild(child, component);
        }
        component(element.expression);
        assert.equal(matches, 1, "Route must render its bound source component");
        paths.push(value);
      }
    }
    ts.forEachChild(node, visit);
  }
  visit(file);
  assert.equal(redirect, 1, "Existing wildcard redirect must remain explicit");
  assert.equal(new Set(paths).size, paths.length, "Duplicate actual Route refused");
  assert.deepEqual([...paths].sort(), Object.keys(screens).sort(), "Every actual SPA route needs an explicit binding");
  return paths;
}

/** Attribution only: the delivered evaluator owns closure, gzip and limit policy. */
export function bindings(manifest, routePaths) {
  assert.deepEqual([...routePaths].sort(), Object.keys(screens).sort(), "Complete current SPA route set required");
  const entries = Object.keys(manifest).filter((key) => manifest[key]?.isEntry);
  assert.deepEqual(entries, ["index.html"], "Exact real served entry required");
  const reachable = new Set();
  function visit(key) {
    if (reachable.has(key)) return;
    assert.ok(Object.hasOwn(manifest, key), `Missing actual manifest reference ${key}`);
    reachable.add(key);
    for (const field of ["imports", "dynamicImports", "css", "assets"]) {
      if (manifest[key][field] !== undefined) assert.ok(Array.isArray(manifest[key][field])
        && manifest[key][field].every((value) => typeof value === "string" && value), "Malformed actual manifest reference");
    }
    for (const dependency of [...manifest[key].imports ?? [], ...manifest[key].dynamicImports ?? []]) visit(dependency);
  }
  visit("index.html");
  for (const key of [account, ...Object.values(screens).filter(Boolean)]) {
    assert.ok(reachable.has(key) && manifest[key].isDynamicEntry === true, `Required source-keyed dynamic root absent: ${key}`);
  }
  const routes = Object.fromEntries(journeys.map((name) => {
    const screen = screens[name.split("?")[0]];
    return [name, { class: "cat-initial", entries: ["index.html", account, ...(screen ? [screen] : [])] }];
  }));
  const globalCss = collectInitialBundleFiles(manifest, { eagerRoots: [account] }).filter((file) => file.endsWith(".css"));
  return { inventory: journeys.map((name) => ({ name, path: name, template: "index.html" })),
    config: { schema: 1, routes, global_css: globalCss, vendors: {} } };
}

export function measureProfile(assetsRoot, budgets, routePaths, api) {
  const manifestBytes = read(assetsRoot, ".vite/manifest.json"), manifest = JSON.parse(manifestBytes);
  const attribution = bindings(manifest, routePaths);
  const report = api.evaluate(budgets, manifest, attribution.inventory, attribution.config, assetsRoot);
  return { manifest_sha256: hash(manifestBytes), ...attribution, report, budgets: api.gateBudgets(report) };
}

/** Require all actual files, not just the bytes that happen to enter a sum. */
export function verifyTreeRows(root, directory, expected) {
  const wanted = new Map();
  for (const item of expected) {
    relative(item.path);
    assert.ok(!wanted.has(item.path) && Number.isSafeInteger(item.bytes) && item.bytes >= 0
      && /^[a-f0-9]{64}$/.test(item.sha256), "Invalid/duplicate asset inventory row");
    wanted.set(item.path, item);
  }
  assert.ok(wanted.size, "Nonempty complete asset inventory required");
  const actual = [];
  function visit(prefix) {
    const base = path.join(root, directory, prefix);
    assert.ok(fs.lstatSync(base).isDirectory() && !fs.lstatSync(base).isSymbolicLink(), "Regular asset directory required");
    for (const name of fs.readdirSync(base).sort()) {
      const file = prefix + name, info = fs.lstatSync(path.join(base, name));
      assert.ok(!info.isSymbolicLink(), "Asset symlink refused");
      if (info.isDirectory()) visit(file + "/");
      else {
        assert.ok(info.isFile(), "Nonregular asset refused");
        const bytes = read(root, directory + "/" + file);
        if (file === ".keep") { assert.equal(bytes.length, 0); continue; }
        actual.push(file);
        assert.deepEqual({ path: file, bytes: bytes.length, sha256: hash(bytes) }, wanted.get(file), "Actual asset differs from complete bound inventory");
      }
    }
  }
  visit("");
  assert.deepEqual(actual.sort(), [...wanted.keys()].sort(), "Missing/extra bound asset refused");
  return expected.map((item) => ({ ...item }));
}

async function main() {
  const root = process.cwd(), target = process.argv[2], invocation = process.argv[3];
  assert.ok(process.platform === "linux" && root === "/work" && ["unit", "full"].includes(target), "Actual owning Linux unit/full required");
  assert.match(invocation ?? "", /^[a-f0-9]{8}-[a-f0-9]{4}-4[a-f0-9]{3}-[89ab][a-f0-9]{3}-[a-f0-9]{12}$/);
  const descriptor = json(root, ".gate/wrapper-current.json");
  assert.equal(descriptor.target, target);
  const captured = json(root, descriptor.config_path), config = captured.config;
  resolveHookRuntime(root, target, config); // existing frozen source/config/SDK admission
  const bootstrapPath = `.gate/${target}/bootstrap-execution.json`, bootstrap = json(root, bootstrapPath);
  // The inner hook and primary wrapper have different genuine UUIDs. Reuse
  // their existing bootstrap link instead of equating or inventing either one.
  assert.equal(bootstrap.invocation, invocation);
  assert.equal(bootstrap.wrapper_invocation, descriptor.invocation);
  assert.equal(bootstrap.wrapper_descriptor_sha256, hash(read(root, ".gate/wrapper-current.json")));
  assert.equal(bootstrap.wrapper_config_sha256, descriptor.config_file_sha256);
  for (const key of ["target", "sha", "tree_sha256", "toolchain_digest"]) assert.equal(bootstrap[key], descriptor[key]);
  const syncPath = `.gate/${target}/managed-assets/sync.json`, sync = json(root, syncPath);
  assert.equal(sync.schema, 1);
  for (const key of ["sha", "tree_sha256", "toolchain_digest"]) assert.equal(sync[key], descriptor[key]);
  const expectedContext = { ...descriptor, descriptor_sha256: hash(read(root, ".gate/wrapper-current.json")) };
  for (const name of ["prepare", "inventory"]) {
    const receipt = json(root, `.gate/${target}/managed-assets/${name}.json`);
    assert.deepEqual(receipt.context, expectedContext, "Fresh actual managed-output invocation required");
    if (name === "inventory") {
      assert.equal(receipt.manifest_sha256, sync.manifest_sha256);
      assert.deepEqual(receipt.files, sync.dist);
    }
  }
  const apiPath = config.npm_dir + "/budget/index.mjs";
  const api = await import(pathToFileURL(regular(root, apiPath)).href);
  const parserPath = "frontend/node_modules/@typescript/typescript6/lib/typescript.js";
  const ts = (await import(pathToFileURL(regular(root, parserPath)).href)).default;
  const parser = parserBinding(path.join(root, "frontend"), ts);
  const routePaths = appRoutePaths(read(root, "frontend/src/App.tsx").toString("utf8"), ts);
  const baseline = json(root, "baselines/cat/capture.json");
  assert.deepEqual(baseline.pages.map((item) => item.route).sort(), journeys.filter((name) => name !== "/alchimie").sort(), "All original frozen journeys must remain measured");
  const proof = json(root, "legacy/original-bundle.json");
  assert.equal(proof.sha256, legacyHash);
  assert.equal(sync.legacy_sha256, legacyHash);
  assert.equal(proof.files.length, 30);
  const archiveBytes = read(root, proof.archive);
  assert.equal(hash(archiveBytes), legacyHash);
  assert.equal(read(root, proof.archive + ".sha256").toString("utf8"), `${legacyHash}  ${path.basename(proof.archive)}\n`);
  const tarPath = config.npm_dir + "/scripts/kit-sync.mjs";
  const { readTarGz } = await import(pathToFileURL(regular(root, tarPath)).href);
  const archive = readTarGz(archiveBytes);
  assert.equal(archive.size, proof.files.length);
  for (const item of proof.files) {
    const entry = archive.get(item.path);
    assert.ok(entry?.type === "file" && entry.data.length === item.bytes && hash(entry.data) === item.sha256, "Exact frozen archive member required");
  }
  const activeRows = verifyTreeRows(root, "frontend/dist", sync.dist);
  verifyTreeRows(root, "go-backend/embedfs/dist", activeRows);
  const legacyRows = verifyTreeRows(root, "go-backend/embedfs/legacy", proof.files);
  assert.deepEqual(sync.legacy, legacyRows);
  const budgets = json(root, "budgets.json");
  const profiles = {};
  for (const [name, directory, assets] of [["active", "go-backend/embedfs/dist", activeRows], ["frozen-legacy", "go-backend/embedfs/legacy", legacyRows]]) {
    profiles[name] = { assets_root: directory, assets,
      ...measureProfile(path.join(root, directory), budgets, routePaths, api) };
  }
  assert.equal(profiles.active.manifest_sha256, sync.manifest_sha256);
  const inputs = ["budgets.json", "versions.lock.json", "frontend/package.json", "frontend/package-lock.json",
    "frontend/index.html", "frontend/src/main.tsx", "frontend/src/App.tsx", "frontend/src/screens/Home.tsx",
    "frontend/src/components/AccountBar.tsx", ...Object.values(screens).filter(Boolean).map((name) => "frontend/" + name),
    "frontend/src/screens/AlchimieExplore.tsx", "baselines/cat/capture.json",
    "legacy/original-bundle.json", proof.archive, proof.archive + ".sha256", syncPath, bootstrapPath,
    `.gate/${target}/managed-assets/prepare.json`, `.gate/${target}/managed-assets/inventory.json`,
    ".gate/wrapper-current.json", `.gate/${target}/wrapper-current.json`, descriptor.config_path,
    "Taskfile.repo.yml", "scripts/gui-route-budgets.mjs", "scripts/gui-repo-hook.mjs",
    "frontend/scripts/check-bundle-budget.mjs", "frontend/scripts/compiler-runtime.mjs", apiPath,
    config.npm_dir + "/schemas/budgets.schema.json", config.npm_dir + "/schemas/validate.mjs", tarPath];
  const result = { schema: 1, check: "cat-route-budgets", target, invocation, wrapper_invocation: descriptor.invocation,
    sha: descriptor.sha, tree_sha256: descriptor.tree_sha256, toolchain_digest: descriptor.toolchain_digest,
    status: Object.values(profiles).every((item) => item.report.status === "pass") ? "pass" : "fail",
    scope: "actual active SPA routes and separately measured frozen-legacy journeys; no runtime/vitals qualification",
    method: "delivered public evaluate/gateBudgets; verified gzip sidecars or level-6 gzip; explicit entry/AccountBar/route static closures",
    budgets_sha256: hash(read(root, "budgets.json")), route_source_paths: routePaths, wildcard_redirect: "/", parser,
    inputs: inputs.map((name) => row(root, name)), profiles,
    budgets: Object.fromEntries(Object.entries(profiles).flatMap(([name, profile]) =>
      Object.entries(profile.budgets).map(([key, value]) => [`${name}:${key}`, value]))) };
  const output = `.gate/${target}/route-budgets`;
  fs.mkdirSync(path.join(root, output), { recursive: true });
  for (const [name, profile] of Object.entries(profiles)) fs.writeFileSync(path.join(root, output, name + ".json"), JSON.stringify(profile, null, 2) + "\n");
  fs.writeFileSync(path.join(root, output, "measurements.json"), JSON.stringify(result, null, 2) + "\n");
  process.stdout.write(JSON.stringify(result) + "\n");
  process.exitCode = result.status === "pass" ? 0 : 1;
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  main().catch((error) => { console.error(error.message); process.exitCode = 1; });
}
