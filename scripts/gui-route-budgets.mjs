import assert from "node:assert/strict";
import * as fs from "node:fs";
import path from "node:path";
import { createHash } from "node:crypto";
import { fileURLToPath, pathToFileURL } from "node:url";
import { gzipSync, gunzipSync } from "node:zlib";
import { collectInitialBundleFiles } from "../frontend/scripts/check-bundle-budget.mjs";
import { parserBinding } from "../frontend/scripts/compiler-runtime.mjs";
import { resolveHookRuntime } from "./gui-hook-runtime.mjs";

const hash = (bytes) => createHash("sha256").update(bytes).digest("hex");
const legacyHash = "742bb11130fa2bf52ba5c64cb9cfd452f7d8ac3a4fd9dc6d77e8064a6b8fef65";
export const frozenBaseline = Object.freeze({
  source: "93066854f67245d4b70c0ea97dc2401445a3218c",
  tree_sha256: "5680879ab9a94f00a64e3815fdbda45b8bc6c5b3dbfd8b02150fa265a3ccbbec",
  toolchain_digest: "sha256:2e040a5165d79be63755424f707fdb8cf609ace831ada7a9baca398ac25e12b9",
  proof_sha256: "5f9897def4020047f9d0fa199ed96b2e52d6facd1cd878da35c65cafb4e78984",
  result_sha256: "b7e861a641817e61af74ecac27ef08818ba7ef138bf676ef588b888c2fda7e25",
  execution_sha256: "240d56636cdef71b27487d40888bd623c176d992500b919f0a141178da7d9c28",
  stdout_sha256: "ab679fc4def1fed43cf29d48364e74f7e14e32739690331edabb3e4a58104bda",
  manifest_sha256: "9ed68d3ff5f73bec7ced96e100ff5718043bcc7efc85cf3b3916df5c82867827",
});
const frozenReceipt = "docs/reviews/gui-original-react/legacy-freeze-9306685";
export const frozenBaselineReferences = Object.freeze(["legacy/original-bundle.json",
  `${frozenReceipt}/result.json`, `${frozenReceipt}/execution.json`,
  `${frozenReceipt}/logs/1c0c864f-beec-4d55-98e0-7a1dec14324c-cat-legacy-freeze-0.stdout.log`]);
const account = "src/components/AccountBar.tsx";
const home = "src/screens/Home.tsx";
// The frozen legacy bundle (ADR-0193 baseline) still carries every original
// screen; the current Preact bundle carries every M3 route with separate lazy
// Alchimie mode leaves (ADR-0202). Each profile binds its own screen table.
const frozenScreens = Object.freeze({
  "/": null,
  "/alchimie": "src/screens/Alchimie.tsx",
  "/intrusul": "src/screens/Intrusul.tsx",
  "/perechi": "src/screens/Perechi.tsx",
  "/cald-rece": "src/screens/CaldRece.tsx",
  "/lant": "src/screens/Lant.tsx",
  "/conexiuni": "src/screens/Conexiuni.tsx",
  "/clasament": "src/screens/Ranking.tsx",
});
export const portedScreens = Object.freeze({
  "/": home,
  "/intrusul": "src/screens/Intrusul.tsx",
  "/perechi": "src/screens/Perechi.tsx",
  "/conexiuni": "src/screens/Conexiuni.tsx",
  "/alchimie": "src/screens/Alchimie.tsx",
  "/cald-rece": "src/screens/CaldRece.tsx",
  "/lant": "src/screens/Lant.tsx",
  "/clasament": "src/screens/Ranking.tsx",
});
const components = { "/": "Home", "/intrusul": "Intrusul", "/perechi": "Perechi", "/conexiuni": "Conexiuni", "/alchimie": "Alchimie", "/cald-rece": "CaldRece", "/lant": "Lant", "/clasament": "Ranking" };
export const alchimieModeScreens = Object.freeze({ challenges: "src/screens/AlchimieChallenge.tsx", explore: "src/screens/AlchimieExplore.tsx" });
// The default /alchimie route is measured too. The two existing baseline
// journeys select different views from its same actual static module closure.
export const journeys = Object.freeze([...Object.keys(frozenScreens),
  "/alchimie?mode=challenges", "/alchimie?mode=explore"]);
export const portedPaths = Object.freeze(Object.keys(portedScreens));
export const portedJourneys = Object.freeze([...portedPaths, "/alchimie?mode=challenges", "/alchimie?mode=explore"]);
export const profiles = Object.freeze({
  active: Object.freeze({ screens: portedScreens, journeys: portedJourneys }),
  "frozen-legacy": Object.freeze({ screens: frozenScreens, journeys }),
});

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

/** Discover the shell's literal route switch, not source substrings or chunk-name guesses. */
export function appRoutePaths(source, ts) {
  const file = ts.createSourceFile("App.tsx", source, ts.ScriptTarget.Latest, true, ts.ScriptKind.TSX);
  assert.equal(file.parseDiagnostics.length, 0, "Current App route source must parse");
  const modules = new Map(), lazyModules = new Set();
  function imports(node) {
    if (ts.isImportDeclaration(node) && ts.isStringLiteral(node.moduleSpecifier)
      && node.importClause?.name) modules.set(node.importClause.name.text, node.moduleSpecifier.text);
    if (ts.isVariableDeclaration(node) && ts.isIdentifier(node.name) && node.initializer
      && ts.isCallExpression(node.initializer) && node.initializer.expression.getText(file) === "lazyScreen") {
      const found = [];
      function dynamic(child) {
        if (ts.isCallExpression(child) && child.expression.kind === ts.SyntaxKind.ImportKeyword) {
          assert.ok(child.arguments.length === 1 && ts.isStringLiteral(child.arguments[0]), "Literal lazy import required");
          found.push(child.arguments[0].text);
        }
        ts.forEachChild(child, dynamic);
      }
      dynamic(node.initializer);
      assert.equal(found.length, 1, "One actual source module per lazy screen required");
      modules.set(node.name.text, found[0]);
      lazyModules.add(node.name.text);
    }
    ts.forEachChild(node, imports);
  }
  imports(file);
  assert.equal(modules.get("AccountBar"), "./components/AccountBar", "Mandatory root must bind its actual module");
  assert.ok(lazyModules.has("Home"), "Home must retain its actual route-lazy boundary");
  for (const [route, component] of Object.entries(components)) {
    const expected = portedScreens[route] ?? "src/screens/Home.tsx";
    assert.equal(modules.get(component), "./" + expected.slice(4, -4), "Route component must bind its real source module");
  }
  function renders(node, name) {
    let matches = 0;
    function component(child) {
      if ((ts.isJsxOpeningElement(child) || ts.isJsxSelfClosingElement(child))
        && child.tagName.getText(file) === name) matches++;
      ts.forEachChild(child, component);
    }
    component(node);
    return matches;
  }
  const paths = [];
  let switches = 0, fallbacks = 0;
  function visit(node) {
    if (ts.isSwitchStatement(node)) {
      switches++;
      // The selector binds each current screen; other document paths go through
      // the explicit current-shell fallback and canonicalize before rendering.
      const selector = node.expression;
      assert.ok(ts.isConditionalExpression(selector) && ts.isCallExpression(selector.condition)
        && selector.condition.expression.getText(file) === "portedPath"
        && ts.isStringLiteral(selector.whenFalse) && selector.whenFalse.text === "fallback", "Route switch must select on the ported-path predicate");
      for (const clause of node.caseBlock.clauses) {
        if (ts.isDefaultClause(clause)) {
          assert.equal(renders(clause, "FallbackRoute"), 1, "Unknown document paths must fall through to the explicit current fallback");
          fallbacks++;
          continue;
        }
        assert.ok(ts.isStringLiteral(clause.expression), "Nonliteral route case refused");
        const value = clause.expression.text;
        assert.ok(Object.hasOwn(components, value), "Unbound actual SPA route refused");
        assert.equal(renders(clause, components[value]), 1, "Route case must render its bound source component");
        paths.push(value);
      }
    }
    ts.forEachChild(node, visit);
  }
  visit(file);
  assert.equal(switches, 1, "Exactly one literal route switch required");
  assert.equal(fallbacks, 1, "Current document fallback must remain explicit");
  assert.equal(new Set(paths).size, paths.length, "Duplicate actual route refused");
  assert.deepEqual([...paths].sort(), Object.keys(portedScreens).sort(), "Every ported SPA route needs an explicit binding");
  return paths;
}

/** Bind both dynamically mounted leaves; a tiny selector alone is not a route budget. */
export function alchimieModeBindings(source, ts) {
  const file = ts.createSourceFile("Alchimie.tsx", source, ts.ScriptTarget.Latest, true, ts.ScriptKind.TSX);
  assert.equal(file.parseDiagnostics.length, 0, "Alchimie selector must parse");
  const expected = { AlchimieChallenge: "./AlchimieChallenge", AlchimieExplore: "./AlchimieExplore" }, found = new Map();
  let calls = 0, selections = 0;
  function visit(node) {
    if (ts.isImportDeclaration(node)) assert.ok(!Object.values(expected).includes(node.moduleSpecifier.text), "A mode leaf cannot be statically imported by its selector");
    if (ts.isCallExpression(node) && node.expression.kind === ts.SyntaxKind.ImportKeyword) calls++;
    if (ts.isVariableDeclaration(node) && ts.isIdentifier(node.name) && Object.hasOwn(expected, node.name.text)) {
      assert.ok(node.initializer && ts.isCallExpression(node.initializer) && node.initializer.expression.getText(file) === "lazyScreen", "Each mode needs the owning lazyScreen boundary");
      const imports = [];
      function inspect(child) {
        if (ts.isCallExpression(child) && child.expression.kind === ts.SyntaxKind.ImportKeyword) imports.push(child);
        ts.forEachChild(child, inspect);
      }
      inspect(node.initializer);
      assert.ok(imports.length === 1 && imports[0].arguments.length === 1 && ts.isStringLiteral(imports[0].arguments[0])
        && imports[0].arguments[0].text === expected[node.name.text], "Mode leaf source differs from its literal import");
      assert.ok(!found.has(node.name.text), "Duplicate mode boundary"); found.set(node.name.text, imports[0].arguments[0].text);
    }
    if (ts.isVariableDeclaration(node) && ts.isIdentifier(node.name) && node.name.text === "mode") {
      assert.equal(node.initializer?.getText(file), "alchimieMode(url, legacyResume)", "Mode must use the frame URL and saved-round snapshot"); selections++;
    }
    if (ts.isCallExpression(node)) assert.notEqual(node.expression.getText(file), "useLocation", "Mode selector cannot follow another frame's live location");
    ts.forEachChild(node, visit);
  }
  visit(file);
  assert.equal(calls, 2); assert.equal(found.size, 2); assert.equal(selections, 1);
  assert.match(source, /return mode === "challenges"\s*\? <AlchimieChallenge\b[^>]*\/>\s*: <AlchimieExplore\b[^>]*\/>;/, "Both selector branches must render their charged mode leaf");
  return { selector: "src/screens/Alchimie.tsx", modes: { ...alchimieModeScreens }, default: "explore", saved_default: "challenges" };
}

/** The three declarations of the ported set must agree: shell, client route table, Go server. */
export function portedSetBindings(root, routePaths) {
  const client = read(root, "frontend/src/routes.ts").toString("utf8");
  const clientList = /PORTED_PATHS = Object\.freeze\(\[([^\]]*)\] as const\)/.exec(client);
  assert.ok(clientList, "Literal client ported-path table required");
  const clientPaths = [...clientList[1].matchAll(/"([^"]*)"/g)].map((match) => match[1]);
  const server = read(root, "go-backend/internal/httpapi/managed_delivery.go").toString("utf8");
  const serverList = /managedPortedRoutes = map\[string\]bool\{([^}]*)\}/.exec(server);
  assert.ok(serverList, "Literal Go ported-route table required");
  const serverPaths = [...serverList[1].matchAll(/"([^"]*)": true/g)].map((match) => match[1]);
  for (const [name, list] of [["client", clientPaths], ["server", serverPaths], ["shell", routePaths]]) {
    assert.deepEqual([...list].sort(), [...portedPaths].sort(), `The ${name} ported set differs from the measured active set`);
  }
  return { ported: [...portedPaths], client: "frontend/src/routes.ts", server: "go-backend/internal/httpapi/managed_delivery.go",
    shell: "frontend/src/App.tsx", frozen_legacy: journeys.filter((name) => !portedPaths.includes(name.split("?")[0])) };
}

/** Attribution only: the delivered evaluator owns closure, gzip and limit policy. */
export function bindings(manifest, routePaths, profile = "active") {
  const { screens, journeys: measured } = profiles[profile];
  assert.deepEqual([...routePaths].sort(), Object.keys(screens).sort(), `Complete ${profile} SPA route set required`);
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
  for (const key of [account, ...Object.values(screens).filter(Boolean), ...(profile === "active" ? Object.values(alchimieModeScreens) : [])]) {
    assert.ok(reachable.has(key) && manifest[key].isDynamicEntry === true, `Required source-keyed dynamic root absent: ${key}`);
  }
  if (profile === "active") {
    const selector = manifest["src/screens/Alchimie.tsx"];
    assert.deepEqual([...(selector.dynamicImports ?? [])].sort(), Object.values(alchimieModeScreens).sort(), "Selector must dynamically select exactly both charged leaves");
    const staticFiles = (key, files = new Set(), seen = new Set()) => {
      if (seen.has(key)) return files;
      seen.add(key); files.add(manifest[key].file);
      for (const dependency of manifest[key].imports ?? []) staticFiles(dependency, files, seen);
      return files;
    };
    const selectorFiles = staticFiles("src/screens/Alchimie.tsx");
    for (const key of ["index.html", account, ...Object.values(screens).filter((key) => key !== home), ...Object.values(alchimieModeScreens)]) {
      assert.ok(!staticFiles(key).has(manifest[home].file), "Home cannot be eagerly loaded by another route or the shared shell");
    }
    for (const [mode, key] of Object.entries(alchimieModeScreens)) {
      assert.ok(!selectorFiles.has(manifest[key].file), "Mode selector eagerly imports a leaf");
      const other = alchimieModeScreens[mode === "challenges" ? "explore" : "challenges"];
      assert.ok(!staticFiles(key).has(manifest[other].file), "One mode eagerly imports the other mode");
    }
  }
  const routes = Object.fromEntries(measured.map((name) => {
    const screen = screens[name.split("?")[0]];
    const mode = profile === "active" && name.split("?")[0] === "/alchimie"
      ? name === "/alchimie?mode=challenges" ? "challenges" : "explore" : null;
    return [name, { class: "cat-initial", entries: ["index.html", account, ...(screen ? [screen] : []), ...(mode ? [alchimieModeScreens[mode]] : [])] }];
  }));
  const globalCss = collectInitialBundleFiles(manifest, { eagerRoots: [account] }).filter((file) => file.endsWith(".css"));
  return { inventory: measured.map((name) => ({ name, path: name, template: "index.html" })),
    config: { schema: 1, routes, global_css: globalCss, vendors: {} } };
}

// App-owned total-CSS policy, separate from the unchanged delivered SDK report.
// Every actual CSS file counts, including unreferenced files in fresh output.
export const CONSUMER_CSS_TOTAL_KEY = "consumer-css-total:all";
export function measureConsumerCssTotal(assetsRoot, limit) {
  assert.ok(Number.isSafeInteger(limit) && limit >= 0, "Finite numeric current CSS total limit required");
  assert.ok(path.isAbsolute(assetsRoot) && path.resolve(assetsRoot) === assetsRoot,
    "Absolute canonical CSS output root required");
  let cursor = path.parse(assetsRoot).root;
  for (const part of assetsRoot.slice(cursor.length).split(path.sep)) {
    cursor = path.join(cursor, part);
    const info = fs.lstatSync(cursor);
    assert.ok(info.isDirectory() && !info.isSymbolicLink() && fs.realpathSync(cursor) === cursor,
      "Regular confined CSS output ancestry required");
  }
  const inventory = () => {
    const files = [];
    function visit(prefix) {
      const directory = prefix ? path.join(assetsRoot, prefix.slice(0, -1)) : assetsRoot;
      const info = fs.lstatSync(directory);
      assert.ok(info.isDirectory() && !info.isSymbolicLink() && fs.realpathSync(directory) === directory,
        "Regular confined CSS directory required");
      for (const name of fs.readdirSync(directory).sort()) {
        const file = relative(prefix + name), absolute = path.join(assetsRoot, file);
        const entry = fs.lstatSync(absolute);
        assert.ok(!entry.isSymbolicLink(), "CSS output symlink refused");
        if (entry.isDirectory()) visit(file + "/");
        else { assert.ok(entry.isFile(), "Nonregular CSS output refused"); files.push(file); }
      }
    }
    visit("");
    return files.sort();
  };
  const all = inventory(), rawFiles = all.filter((file) => /\.css$/i.test(file));
  assert.ok(rawFiles.length, "Nonempty actual CSS inventory required");
  const rawSet = new Set(rawFiles);
  for (const file of all.filter((file) => /\.css\.gz$/i.test(file))) {
    assert.ok(rawSet.has(file.slice(0, -3)), "CSS gzip sidecar without raw CSS refused");
  }
  const acquire = (file) => {
    const absolute = regular(assetsRoot, file), previous = fs.lstatSync(absolute, { bigint: true });
    const fd = fs.openSync(absolute, fs.constants.O_RDONLY | fs.constants.O_NOFOLLOW);
    try {
      const opened = fs.fstatSync(fd, { bigint: true }), bytes = fs.readFileSync(fd), after = fs.fstatSync(fd, { bigint: true });
      assert.ok(opened.isFile() && opened.dev === previous.dev && opened.ino === previous.ino
        && ["dev", "ino", "mode", "size", "mtimeNs", "ctimeNs"].every((key) => opened[key] === after[key])
        && BigInt(bytes.length) === after.size, "CSS asset changed during acquisition");
      return bytes;
    } finally { fs.closeSync(fd); }
  };
  const files = rawFiles.map((file) => {
    const raw = acquire(file), sidecar = file + ".gz";
    assert.ok(all.includes(sidecar), "Missing canonical CSS gzip sidecar");
    const compressed = acquire(sidecar);
    let restored;
    try { restored = gunzipSync(compressed, { maxOutputLength: raw.length + 1 }); }
    catch { throw new Error("Invalid CSS gzip sidecar"); }
    assert.ok(restored.equals(raw), "Stale CSS gzip sidecar");
    assert.ok(compressed.equals(gzipSync(raw, { level: 9 })), "Noncanonical level-9 CSS gzip sidecar");
    return { file, bytes: raw.length, sha256: hash(raw), gzip: { file: sidecar, bytes: compressed.length, sha256: hash(compressed) } };
  });
  assert.deepEqual(inventory(), all, "CSS output membership changed during measurement");
  const actual = files.reduce((sum, item) => sum + item.gzip.bytes, 0);
  return { schema: 1, status_source: "consumer-css-total", scope: "all-actual-current-css",
    status: actual <= limit ? "pass" : "fail", limit_gz: limit, actual_gz: actual,
    compression: "canonical-gzip-level9", inventory_sha256: hash(JSON.stringify(all)), files };
}

export function measureProfile(assetsRoot, budgets, routePaths, api, profile = "active") {
  const manifestBytes = read(assetsRoot, ".vite/manifest.json"), manifest = JSON.parse(manifestBytes);
  const attribution = bindings(manifest, routePaths, profile);
  const report = api.evaluate(budgets, manifest, attribution.inventory, attribution.config, assetsRoot);
  const sdkBudgets = api.gateBudgets(report);
  // Frozen original30 files have no sidecars and remain byte-exact. Their raw
  // SDK profile keeps its existing gzip-fallback measurements and baseline projection.
  const consumerCssTotal = profile === "active"
    ? measureConsumerCssTotal(assetsRoot, budgets.css.global.limit_gz) : null;
  const consumerBudgets = consumerCssTotal ? { [CONSUMER_CSS_TOTAL_KEY]: {
    limit: consumerCssTotal.limit_gz, actual: consumerCssTotal.actual_gz, status: consumerCssTotal.status,
    status_source: consumerCssTotal.status_source, inventory_sha256: consumerCssTotal.inventory_sha256,
  } } : {};
  const status = report.status === "pass" && (!consumerCssTotal || consumerCssTotal.status === "pass") ? "pass" : "fail";
  return { status, manifest_sha256: hash(manifestBytes), ...attribution, report, sdk_budgets: sdkBudgets,
    consumer_css_total: consumerCssTotal, budgets: { ...sdkBudgets, ...consumerBudgets } };
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

/** Reuse the genuine freeze receipt/archive and the existing complete-tree check. */
export function verifyFrozenBaseline(root, sync, readTarGz) {
  const proofBytes = read(root, frozenBaselineReferences[0]);
  assert.equal(hash(proofBytes), frozenBaseline.proof_sha256, "Original producer proof identity required");
  const proof = JSON.parse(proofBytes);
  for (const key of ["tree_sha256", "toolchain_digest"]) assert.equal(proof[key], frozenBaseline[key]);
  assert.equal(proof.schema, 1); assert.equal(proof.sha, frozenBaseline.source);
  assert.equal(proof.archive, `legacy/cat_de_roman_esti-legacy-${frozenBaseline.source}.tgz`);
  assert.equal(proof.sha256, legacyHash); assert.equal(sync.legacy_sha256, legacyHash);
  const resultBytes = read(root, frozenBaselineReferences[1]), executionBytes = read(root, frozenBaselineReferences[2]);
  assert.equal(hash(resultBytes), frozenBaseline.result_sha256, "Genuine original freeze result required");
  assert.equal(hash(executionBytes), frozenBaseline.execution_sha256, "Genuine original producer execution required");
  const result = JSON.parse(resultBytes), execution = JSON.parse(executionBytes);
  assert.equal(result.target, "legacy:freeze"); assert.equal(result.status, "pass"); assert.equal(result.dirty, false);
  for (const value of [result, execution]) {
    assert.equal(value.sha, frozenBaseline.source);
    assert.equal(value.tree_sha256, frozenBaseline.tree_sha256);
  }
  assert.equal(result.toolchain_digest, frozenBaseline.toolchain_digest);
  assert.ok(result.checks.every((item) => item.status === "pass"));
  const producer = execution.actions.filter((item) => item.check === "cat-legacy-freeze" && item.kind === "command");
  assert.equal(producer.length, 1); assert.equal(producer[0].command, "node"); assert.equal(producer[0].exit_code, 0);
  const stdout = read(root, frozenBaselineReferences[3]);
  assert.equal(hash(stdout), frozenBaseline.stdout_sha256); assert.equal(producer[0].stdout_sha256, hash(stdout));
  assert.deepEqual(JSON.parse(stdout), proof, "Actual freeze stdout must bind the original proof");
  assert.equal(proof.files.length, 30);
  const archiveBytes = read(root, proof.archive);
  assert.equal(hash(archiveBytes), legacyHash);
  const sidecar = read(root, proof.archive + ".sha256");
  assert.equal(sidecar.toString("utf8"), `${legacyHash}  ${path.basename(proof.archive)}\n`);
  for (const [name, digest] of [[proof.archive, legacyHash], [proof.archive + ".sha256", hash(sidecar)],
    ["legacy/original-bundle.json", hash(proofBytes)], [".gate/legacy-freeze/execution.json", hash(executionBytes)]]) {
    assert.ok(result.artifacts.includes(`${name} sha256:${digest}`), "Original result must own each frozen input");
  }
  const archive = readTarGz(archiveBytes);
  assert.equal(archive.size, proof.files.length);
  for (const item of proof.files) {
    const entry = archive.get(item.path);
    assert.ok(entry?.type === "file" && entry.data.length === item.bytes && hash(entry.data) === item.sha256, "Exact frozen archive member required");
  }
  const files = verifyTreeRows(root, "go-backend/embedfs/legacy", proof.files);
  assert.deepEqual(sync.legacy, files);
  assert.equal(hash(read(root, "go-backend/embedfs/legacy/.vite/manifest.json")), frozenBaseline.manifest_sha256);
  return { schema: 1, status: "pass", classification: "frozen-baseline-integrity", ...frozenBaseline,
    archive: proof.archive, archive_sha256: legacyHash, files,
    required_full_runtime_checks: ["cat-legacy-owner-journey", "cat-browser-full"],
    scope: "Original artifact integrity only; actual full fallback journey and every safety check remain mandatory" };
}

/** Owner-approved consumer classification; the delivered SDK reports stay untouched.
 * Active rows gate exactly the ported set the server serves from the current
 * bundle; every other journey is served by the frozen legacy bundle and keeps
 * its recorded baseline row (ADR-0193 projection), never a raised or absent limit. */
export function classifyProfiles(measuredProfiles, integrity, target) {
  assert.ok(["unit", "full"].includes(target));
  assert.deepEqual(Object.keys(measuredProfiles).sort(), ["active", "frozen-legacy"]);
  assert.equal(integrity?.status, "pass"); assert.equal(integrity.classification, "frozen-baseline-integrity");
  for (const [key, value] of Object.entries(frozenBaseline)) assert.equal(integrity[key], value);
  assert.equal(integrity.archive_sha256, legacyHash); assert.equal(integrity.files.length, 30);
  const qualified = {};
  for (const [name, profile] of Object.entries(measuredProfiles)) {
    const expected = profiles[name].journeys;
    assert.equal(profile.report.routes.length, expected.length);
    assert.deepEqual(profile.report.routes.map((item) => item.name).sort(), [...expected].sort());
    for (const [key, value] of Object.entries(profile.budgets)) {
      const active = name === "active", consumer = key === CONSUMER_CSS_TOTAL_KEY;
      assert.ok(consumer ? value.status_source === "consumer-css-total" : !Object.hasOwn(value, "status_source"),
        "Consumer CSS evidence cannot be relabeled as SDK evidence");
      if (consumer) {
        const total = profile.consumer_css_total;
        assert.ok(active && total?.status_source === "consumer-css-total"
          && value.status_source === "consumer-css-total"
          && value.actual === total.actual_gz && value.limit === total.limit_gz && value.status === total.status
          && value.inventory_sha256 === total.inventory_sha256
          && value.status === (value.actual <= value.limit ? "pass" : "fail"), "Current consumer CSS total binding differs");
      }
      qualified[`${active ? "gate" : "baseline"}:${name}:${key}`] = { ...value,
        status: active ? value.status : "recorded",
        ...(consumer ? { consumer_status: value.status,
          classification: "active-consumer-numeric-gate", consumer_report: `.gate/${target}/route-budgets/${name}.json` }
          : { sdk_status: value.status, classification: active ? "active-numeric-gate" : "frozen-baseline-measurement",
            raw_report: `.gate/${target}/route-budgets/${name}.json` }),
        ...(active ? {} : { integrity_check: "cat-frozen-legacy-integrity" }) };
    }
  }
  assert.ok(Object.hasOwn(measuredProfiles.active.budgets, CONSUMER_CSS_TOTAL_KEY), "Current consumer CSS total row required");
  const gateBudgets = Object.fromEntries(Object.entries(qualified).filter(([name]) => name.startsWith("gate:active:")));
  for (const name of portedJourneys) assert.ok(Object.hasOwn(gateBudgets, `gate:active:route-js:${name}`), `Active route row missing: ${name}`);
  const delivery = Object.fromEntries(journeys.map((name) => [name, portedPaths.includes(name.split("?")[0]) ? "current" : "frozen-legacy"]));
  return { status: measuredProfiles.active.report.status === "pass"
      && measuredProfiles.active.consumer_css_total?.status === "pass" ? "pass" : "fail", budgets: qualified, gate_budgets: gateBudgets,
    delivery, ported_routes: [...portedPaths], frozen_legacy_routes: journeys.filter((name) => delivery[name] === "frozen-legacy"),
    policy: "owner-approved-frozen-legacy-baseline-2026-10-11",
    authority: ["docs/adr/0193-frozen-legacy-budget-baseline.md", "docs/adr/0197-per-route-current-frozen-delivery.md"] };
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
  const modeBindings = alchimieModeBindings(read(root, "frontend/src/screens/Alchimie.tsx").toString("utf8"), ts);
  const portedSet = portedSetBindings(root, routePaths);
  const baseline = json(root, "baselines/cat/capture.json");
  assert.deepEqual(baseline.pages.map((item) => item.route).sort(), journeys.filter((name) => name !== "/alchimie").sort(), "All original frozen journeys must remain measured");
  const tarPath = config.npm_dir + "/scripts/kit-sync.mjs";
  const { readTarGz } = await import(pathToFileURL(regular(root, tarPath)).href);
  const frozenIntegrity = verifyFrozenBaseline(root, sync, readTarGz);
  const proof = json(root, "legacy/original-bundle.json");
  const activeRows = verifyTreeRows(root, "frontend/dist", sync.dist);
  verifyTreeRows(root, "go-backend/embedfs/dist", activeRows);
  const legacyRows = frozenIntegrity.files;
  const budgets = json(root, "budgets.json");
  const measured = {};
  for (const [name, directory, assets, paths] of [["active", "go-backend/embedfs/dist", activeRows, routePaths],
    ["frozen-legacy", "go-backend/embedfs/legacy", legacyRows, Object.keys(frozenScreens)]]) {
    measured[name] = { assets_root: directory, assets,
      ...measureProfile(path.join(root, directory), budgets, paths, api, name) };
  }
  assert.equal(measured.active.manifest_sha256, sync.manifest_sha256);
  const qualification = classifyProfiles(measured, frozenIntegrity, target);
  const inputs = ["budgets.json", "versions.lock.json", "frontend/package.json", "frontend/package-lock.json",
    "frontend/index.html", "frontend/src/main.tsx", "frontend/src/App.tsx", "frontend/src/routes.ts", "frontend/src/homeCardBlur.ts",
    "frontend/src/components/AccountBar.tsx", ...Object.values(portedScreens).filter(Boolean).map((name) => "frontend/" + name),
    ...Object.values(alchimieModeScreens).map((name) => "frontend/" + name), "frontend/src/alchimieMode.ts", "frontend/src/alchimieSavedMode.ts", "frontend/src/lazyScreen.ts", "frontend/src/screenLocation.ts",
    "go-backend/internal/httpapi/managed_delivery.go", "baselines/cat/capture.json",
    ...frozenBaselineReferences, proof.archive, proof.archive + ".sha256", syncPath, bootstrapPath,
    `.gate/${target}/managed-assets/prepare.json`, `.gate/${target}/managed-assets/inventory.json`,
    ".gate/wrapper-current.json", `.gate/${target}/wrapper-current.json`, descriptor.config_path,
    "Taskfile.repo.yml", "scripts/gui-route-budgets.mjs", "scripts/gui-repo-hook.mjs",
    "frontend/scripts/check-bundle-budget.mjs", "frontend/scripts/compiler-runtime.mjs", apiPath,
    config.npm_dir + "/schemas/budgets.schema.json", config.npm_dir + "/schemas/validate.mjs", tarPath];
  const result = { schema: 1, check: "cat-route-budgets", target, invocation, wrapper_invocation: descriptor.invocation,
    sha: descriptor.sha, tree_sha256: descriptor.tree_sha256, toolchain_digest: descriptor.toolchain_digest,
    status: qualification.status, raw_sdk_aggregate_status: Object.values(measured).every((item) => item.report.status === "pass") ? "pass" : "fail",
    qualification, frozen_integrity: frozenIntegrity, ported_set: portedSet, mode_bindings: modeBindings,
    scope: "all current M3 SPA journeys with selected Alchimie mode closures; frozen rollback measured separately; no runtime/vitals qualification",
    method: "delivered public evaluate/gateBudgets; verified gzip sidecars or level-6 gzip; explicit entry/AccountBar/route static closures",
    budgets_sha256: hash(read(root, "budgets.json")), route_source_paths: routePaths, legacy_fallback: "explicit CAT_UI=legacy rollback only; normal managed documents use the current M3 shell (ADR-0202)", parser,
    inputs: inputs.map((name) => row(root, name)), profiles: measured,
    budgets: Object.fromEntries(Object.entries(measured).flatMap(([name, profile]) =>
      Object.entries(profile.budgets).map(([key, value]) => [`${name}:${key}`, value]))) };
  const output = `.gate/${target}/route-budgets`;
  fs.mkdirSync(path.join(root, output), { recursive: true });
  fs.writeFileSync(path.join(root, output, "frozen-integrity.json"), JSON.stringify(frozenIntegrity, null, 2) + "\n");
  fs.writeFileSync(path.join(root, output, "gate-summary.json"), JSON.stringify(qualification, null, 2) + "\n");
  for (const [name, profile] of Object.entries(measured)) fs.writeFileSync(path.join(root, output, name + ".json"), JSON.stringify(profile, null, 2) + "\n");
  fs.writeFileSync(path.join(root, output, "measurements.json"), JSON.stringify(result, null, 2) + "\n");
  process.stdout.write(JSON.stringify(result) + "\n");
  process.exitCode = result.status === "pass" ? 0 : 1;
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  main().catch((error) => { console.error(error.message); process.exitCode = 1; });
}
