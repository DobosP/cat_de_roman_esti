// Actual isolated React19 projected-layout regression. The original Framer12 and
// normalized Motion/Framer14 graphs have separate exact admission; neither graph
// is an execution receipt. This explicit lane stays outside default discovery.
import test from "node:test";
import assert from "node:assert/strict";
import * as fs from "node:fs";
import path from "node:path";
import { createHash, randomUUID } from "node:crypto";
import { createServer } from "node:http";

const hash = (bytes) => createHash("sha256").update(bytes).digest("hex");
const HEX = /^[a-f0-9]{64}$/;
const UUID = /^[a-f0-9]{8}-[a-f0-9]{4}-4[a-f0-9]{3}-[89ab][a-f0-9]{3}-[a-f0-9]{12}$/;
const CSP = "default-src 'none'; script-src 'self'; style-src 'self'; style-src-attr 'none'; img-src 'self' data:; font-src 'self'; connect-src 'none'; base-uri 'none'; form-action 'none'; frame-ancestors 'none'";
const variants = ["original", "broken-cssom", "corrected"];
const closed = (value, fields, optional = []) => value && typeof value === "object" && !Array.isArray(value)
  && fields.every((key) => Object.hasOwn(value, key)) && Object.keys(value).every((key) => fields.includes(key) || optional.includes(key));

function admit() {
  assert.equal(process.platform, "linux");
  assert.equal(process.cwd(), "/work/frontend", "Actual native frontend cwd required; no alternate-root fixtures");
  assert.equal(import.meta.url, "file:///work/frontend/testdata/motion-layout-shadow/runner.test.mjs");
  const root = "/work", uid = process.getuid(), rootStat = fs.lstatSync(root, { bigint: true });
  assert.equal(rootStat.uid, BigInt(uid));
  assert.equal(fs.realpathSync.native(root), root); assert.ok(!rootStat.isSymbolicLink());
  const inputs = new Map();
  function regular(relative, directory = false) {
    assert.ok(typeof relative === "string" && relative && !relative.startsWith("/") && !Array.from(relative).some((character) => { const code = character.charCodeAt(0); return code === 92 || code === 58 || code <= 31; }));
    const parts = relative.split("/"); assert.ok(parts.every((part) => /^[A-Za-z0-9_@.-]+$/.test(part) && ![".", ".."].includes(part)));
    let file = root;
    for (let index = 0; index < parts.length; index++) {
      file = path.join(file, parts[index]); const stat = fs.lstatSync(file, { bigint: true });
      assert.ok(!stat.isSymbolicLink() && (index < parts.length - 1 || directory ? stat.isDirectory() : stat.isFile()));
      assert.equal(stat.dev, rootStat.dev); assert.equal(fs.realpathSync.native(file), file);
    }
    return file;
  }
  function read(relative) {
    const file = regular(relative), before = fs.lstatSync(file, { bigint: true }); assert.equal(before.nlink, 1n);
    const fd = fs.openSync(file, fs.constants.O_RDONLY | fs.constants.O_NOFOLLOW);
    try {
      const opened = fs.fstatSync(fd, { bigint: true }), bytes = fs.readFileSync(fd), after = fs.lstatSync(file, { bigint: true });
      for (const key of ["dev", "ino", "size", "mtimeNs", "ctimeNs", "mode", "uid", "nlink"]) {
        assert.equal(opened[key], before[key]); assert.equal(after[key], before[key]);
      }
      assert.equal(BigInt(bytes.length), before.size);
      if (inputs.has(relative)) assert.deepEqual(inputs.get(relative), bytes, "Repeated execution input changed");
      else inputs.set(relative, bytes);
      return bytes;
    } finally { fs.closeSync(fd); }
  }
  const descriptorBytes = read(".gate/wrapper-current.json"), actual = JSON.parse(descriptorBytes);
  assert.ok(closed(actual, ["schema", "invocation", "target", "sha", "tree_sha256", "toolchain_digest", "config_sha256", "config_path", "config_file_sha256"]));
  assert.equal(actual.schema, 1); assert.ok(["gen", "unit", "full"].includes(actual.target)); assert.match(actual.invocation, UUID);
  assert.match(actual.sha, /^[a-f0-9]{40}(?:[a-f0-9]{24})?$/); assert.match(actual.tree_sha256, HEX);
  assert.match(actual.toolchain_digest, /^sha256:[a-f0-9]{64}$/); assert.match(actual.config_sha256, HEX);
  assert.equal(actual.sha, process.env.GATE_SHA); assert.equal(actual.tree_sha256, process.env.GATE_TREE_SHA256);
  assert.equal(actual.toolchain_digest, process.env.TOOLCHAIN_DIGEST); assert.ok(["true", "false"].includes(process.env.GATE_DIRTY));
  assert.equal(process.env.GATE_VERSIONS_RESOLVE, "0");
  const prefix = `.gate/${actual.target}/`;
  assert.deepEqual(read(prefix + "wrapper-current.json"), descriptorBytes);
  assert.equal(actual.config_path, prefix + "wrapper-kit-config.json"); assert.match(actual.config_file_sha256, HEX);
  const configBytes = read(actual.config_path), captured = JSON.parse(configBytes);
  assert.equal(hash(configBytes), actual.config_file_sha256);
  assert.ok(closed(captured, ["schema", "target", "sha", "tree_sha256", "toolchain_digest", "config", "config_sha256", "command"]));
  for (const key of ["schema", "target", "sha", "tree_sha256", "toolchain_digest", "config_sha256"]) assert.equal(captured[key], actual[key]);
  const config = captured.config;
  assert.ok(closed(config, ["role", "app", "npm_dir", "vendor_dir", "go_dirs"], ["ui_adoption"]));
  assert.equal(config.role, "consumer"); assert.equal(config.app, "cat_de_roman_esti");
  assert.equal(hash(JSON.stringify(config)), actual.config_sha256);
  assert.ok(closed(captured.command, ["command", "args", "exit_code", "duration_ms", "stdout_sha256", "stderr_sha256"]));
  assert.equal(captured.command.command, "task"); assert.deepEqual(captured.command.args, ["--silent", "repo:kit-config"]);
  assert.equal(captured.command.exit_code, 0); assert.match(captured.command.stdout_sha256, HEX); assert.match(captured.command.stderr_sha256, HEX);
  for (const file of [".gate/wrapper-current.json", prefix + "wrapper-current.json", actual.config_path]) {
    const stat = fs.lstatSync(regular(file)); assert.equal(stat.uid, uid); assert.equal(stat.mode & 0o222, 0);
  }
  let request;
  if (actual.target === "gen") {
    request = JSON.parse(read("scripts/gui-gen-request.json"));
    assert.ok(closed(request, ["schema", "operation", "fixtures"])); assert.equal(request.schema, 1);
    assert.ok(["plan-original-styles", "plan-normalized-styles"].includes(request.operation)); assert.equal(request.fixtures, "frontend/e2e/original/runtime.spec.mjs");
  }
  const bootstrap = JSON.parse(read(prefix + "bootstrap-execution.json"));
  assert.ok(closed(bootstrap, ["schema", "target", "invocation", "sha", "tree_sha256", "toolchain_digest", "started", "config", "config_sha256", "wrapper_target", "wrapper_config", "wrapper_config_sha256", "wrapper_invocation", "wrapper_descriptor", "wrapper_descriptor_sha256", "actions", "artifacts", "finished"]));
  for (const key of ["schema", "target", "sha", "tree_sha256", "toolchain_digest", "config_sha256"]) assert.equal(bootstrap[key], actual[key]);
  assert.match(bootstrap.invocation, UUID); assert.equal(bootstrap.wrapper_invocation, actual.invocation);
  assert.equal(bootstrap.wrapper_target, actual.target); assert.equal(bootstrap.wrapper_config, actual.config_path);
  assert.equal(bootstrap.wrapper_config_sha256, actual.config_file_sha256);
  assert.equal(bootstrap.wrapper_descriptor, ".gate/wrapper-current.json"); assert.equal(bootstrap.wrapper_descriptor_sha256, hash(descriptorBytes));
  assert.deepEqual(bootstrap.config, config); assert.ok(bootstrap.actions.length > 0);
  assert.ok(Number.isFinite(Date.parse(bootstrap.started)) && Date.parse(bootstrap.finished) >= Date.parse(bootstrap.started));
  const listed = new Map(), used = new Set();
  for (const artifact of bootstrap.artifacts) {
    const match = /^(.+) sha256:([a-f0-9]{64})$/.exec(artifact);
    assert.ok(match && match[1].startsWith(prefix + "logs/" + bootstrap.invocation + "-bootstrap-") && !listed.has(match[1]));
    assert.equal(hash(read(match[1])), match[2]); listed.set(match[1], match[2]);
  }
  let configurationWitnesses = 0;
  for (const action of bootstrap.actions) {
    assert.equal(action.kind, "command"); assert.equal(action.cwd, "."); assert.equal(action.exit_code, 0);
    assert.ok(Number.isInteger(action.duration_ms) && action.duration_ms >= 0); assert.match(action.args_sha256, HEX);
    for (const stream of ["stdout", "stderr"]) {
      const file = action[stream + "_log"]; assert.equal(listed.get(file), action[stream + "_sha256"]);
      assert.ok(!used.has(file)); used.add(file);
    }
    if (action.phase === "config") {
      assert.equal(action.command, "task"); assert.equal(action.argument_count, 2);
      assert.equal(action.args_sha256, hash(JSON.stringify(["--silent", "repo:kit-config"])));
      assert.deepEqual(JSON.parse(read(action.stdout_log)), config); configurationWitnesses++;
    }
  }
  assert.equal(used.size, listed.size); assert.equal(listed.size, bootstrap.actions.length * 2); assert.ok(configurationWitnesses > 0);
  const versions = {};
  const manifestBytes = read("frontend/package.json"), lockBytes = read("frontend/package-lock.json");
  const graphProfile = hash(manifestBytes) === "43134fe8197aff7aa3ebd816b2e413591d5479de463d3e73f7ce5bf85e8b1b1a" ? "normalized" : "original";
  assert.equal(hash(manifestBytes), graphProfile === "normalized" ? "43134fe8197aff7aa3ebd816b2e413591d5479de463d3e73f7ce5bf85e8b1b1a" : "efde2d3fbdebc5899dc63ca6b518cab0d60370ef36a7301477da720f4978e2e9");
  assert.equal(hash(lockBytes), graphProfile === "normalized" ? "78ba37afe99d18ebcb6a4be54eaab28d2b7084d0a2cc32ae476c0a20ca7224a2" : "f72661b4bd7ad129a6771037bf900a616a0fdf84bbb41f70c6d118b69fb1b62c");
  if (request) assert.equal(request.operation, graphProfile === "normalized" ? "plan-normalized-styles" : "plan-original-styles", "Actual graph must agree with explicit GEN request");
  const manifest = JSON.parse(manifestBytes), lock = JSON.parse(lockBytes);
  assert.equal(manifest.dependencies["@roedu/ui"], "file:vendor/roedu-ui-0.3.0.tgz");
  const motionVersion = graphProfile === "normalized" ? "14.0.0" : "12.42.2", packages = {};
  for (const [name, version] of [["react", "19.2.7"], ["react-dom", "19.2.7"], ["framer-motion", motionVersion], ["motion-dom", motionVersion], ...(graphProfile === "normalized" ? [["motion", "14.0.0"], ["typescript", "7.0.2"], ["@typescript/typescript6", "6.0.2"]] : [])]) {
    const installed = JSON.parse(read(`frontend/node_modules/${name}/package.json`));
    assert.equal(installed.name, name); assert.equal(installed.version, version); const locked = lock.packages[`node_modules/${name}`]; assert.equal(locked.version, version); versions[name] = version;
    packages[name] = { version, resolved: locked.resolved, integrity: locked.integrity };
  }
  if (graphProfile === "normalized") {
    const selected = JSON.parse(read("versions.lock.json")).tools;
    for (const name of ["motion", "framer-motion", "typescript", "@typescript/typescript6"]) assert.equal(selected.find((item) => item.tool === name)?.version, versions[name]);
    const approval = selected.find((item) => item.tool === "@typescript/typescript6"); assert.equal(approval.status, "optional"); assert.ok(approval.exception && approval.approved_by);
    assert.equal(manifest.dependencies.motion, "14.0.0"); assert.ok(!Object.hasOwn(manifest.dependencies, "framer-motion"));
    assert.equal(lock.packages["node_modules/motion"].dependencies["framer-motion"], "14.0.0");
    const implementation = JSON.parse(read("frontend/node_modules/@typescript/old/package.json")); assert.equal(implementation.name, "typescript"); assert.equal(implementation.version, "6.0.3");
    assert.equal(lock.packages["node_modules/@typescript/old"].version, "6.0.3");
    assert.equal(hash(read("frontend/node_modules/@typescript/old/lib/typescript.js")), "569177652966bd528c319171c7dd22860dbf72bde116cbc4f644f1d02bb12e39");
    assert.equal(hash(read("frontend/node_modules/@typescript/typescript6/lib/typescript.js")), "d3f3cd2b04b7f466f4484df921b744223f7bd1f3e353ec9110bdf52695b983d5");
    const phase = config.ui_adoption; assert.ok(closed(phase, ["mode", "until", "legacy"])); assert.equal(phase.mode, "staged-react"); assert.equal(phase.until, "S1-M2");
    assert.equal(phase.legacy.version, "0.3.0"); assert.equal(phase.legacy.archive_sha256, "1934a81cdfd737a051f591ebcae072f5028943b715456dbb2899b483d399c244");
    assert.equal(hash(read(phase.legacy.receipt)), phase.legacy.receipt_sha256);
    for (const [file, expected] of Object.entries({
      "frontend/node_modules/framer-motion/dist/es/index.mjs": "1304c50c9bb56e616959998b3d247049c8c1279806d3b5706d3b7d1a80108b5a",
      "frontend/node_modules/motion-dom/dist/es/projection/styles/scale-box-shadow.mjs": "eec966af20266e1907d5701768d0ca70a77a6ae3801826914db2102347fc866b",
      "frontend/node_modules/motion-dom/dist/es/render/utils/is-forced-motion-value.mjs": "04e32214cd575b08916b7a403d624bc45db7d65f25f7416cb825fc1b027b1adc",
      "frontend/node_modules/motion-dom/dist/es/render/html/utils/scrape-motion-values.mjs": "2e2612169302fcdc1de8583420a2bdfa1075669ab9dd05341a4c3a87454a45b9",
      "frontend/node_modules/motion-dom/dist/es/projection/node/create-projection-node.mjs": "4af19d2ad9f029f8f94459e57ba0879ff99477ebbb5dba9da830de99ce562736",
    })) assert.equal(hash(read(file)), expected, `Actual captured Motion14 payload differs: ${file}`);
  }
  assert.equal(JSON.parse(read("frontend/node_modules/@roedu/ui/package.json")).version, "0.3.0"); versions["@roedu/ui"] = "0.3.0";
  assert.equal(JSON.parse(read("frontend/node_modules/@playwright/test/package.json")).version, "1.63.0");
  assert.equal(JSON.parse(read("frontend/node_modules/playwright/package.json")).version, "1.63.0");
  for (const name of ["vite", "@vitejs/plugin-react"]) versions[name] = JSON.parse(read(`frontend/node_modules/${name}/package.json`)).version;
  assert.equal(hash(read("frontend/vendor/roedu-ui-0.3.0.tgz")), "1934a81cdfd737a051f591ebcae072f5028943b715456dbb2899b483d399c244");
  for (const file of ["frontend/testdata/motion-layout-shadow/index.html", "frontend/testdata/motion-layout-shadow/tsconfig.json", "frontend/testdata/motion-layout-shadow/entry.tsx", "frontend/testdata/motion-layout-shadow/fixture.css", "frontend/testdata/motion-layout-shadow/runner.test.mjs", "frontend/src/components/CspStyle.ts", "frontend/src/components/CspElements.tsx", "frontend/src/components/cssUnits.ts", "frontend/src/styles/csp-style.css", "frontend/src/styles/arcade.css", "frontend/src/styles/conexiuni.css", "frontend/src/styles/contexto.css", "frontend/src/theme.ts", "frontend/src/games.ts", "frontend/src/screens/Conexiuni.tsx", "frontend/src/screens/CaldRece.tsx", "frontend/node_modules/@roedu/ui/dist/index.js", "frontend/node_modules/motion-dom/dist/es/projection/styles/scale-box-shadow.mjs", "frontend/node_modules/motion-dom/dist/es/projection/styles/scale-correction.mjs", "frontend/node_modules/motion-dom/dist/es/render/utils/is-forced-motion-value.mjs", "frontend/node_modules/motion-dom/dist/es/render/html/utils/scrape-motion-values.mjs", "frontend/node_modules/motion-dom/dist/es/projection/node/create-projection-node.mjs"]) read(file);
  const conex = read("frontend/src/screens/Conexiuni.tsx").toString(), cald = read("frontend/src/screens/CaldRece.tsx").toString();
  assert.ok(conex.includes('boxShadow: isSel ? `0 0 18px -6px ${DEF.accent}` : undefined'));
  assert.ok(cald.includes('boxShadow: isLatest ? `0 0 22px -10px ${color}` : undefined'));
  assert.ok(conex.includes('"card center connection-tile"') && conex.includes("                    layout"));
  assert.ok(cald.includes('"card contexto-guess-row"') && cald.includes("      layout"));
  assert.ok(read("frontend/src/games.ts").toString().includes('accent: "#54e39d"'));
  assert.ok(cald.includes('Cald: "#f4a259"'));
  return { root, uid, actual, read, regular, inputs, versions, packages, graphProfile, scope: "focused original Motion style.boxShadow ownership model with SDK CSSOM rest; not full-game parity; current App domAnimation is not projected" };
}

function shadow(css) {
  assert.equal(typeof css, "string");
  const tokens = css.trim().match(/rgba?\([^()]*\)|[^\s]+/gi) ?? [];
  assert.equal(tokens.length, 5, "Single color and exactly four owner-shadow lengths required");
  const color = (token) => {
    if (/^#(?:[a-f0-9]{3}|[a-f0-9]{4}|[a-f0-9]{6}|[a-f0-9]{8})$/i.test(token)) return true;
    const match = /^(rgb|rgba)\(\s*([\d.]+)\s*,\s*([\d.]+)\s*,\s*([\d.]+)(?:\s*,\s*([\d.]+))?\s*\)$/i.exec(token);
    if (!match || (match[1].toLowerCase() === "rgba") !== (match[5] !== undefined)) return false;
    return match.slice(2, 5).every((value) => Number.isFinite(Number(value)) && Number(value) >= 0 && Number(value) <= 255)
      && (match[5] === undefined || Number.isFinite(Number(match[5])) && Number(match[5]) >= 0 && Number(match[5]) <= 1);
  };
  const colorIndices = tokens.flatMap((token, index) => color(token) ? [index] : []);
  assert.equal(colorIndices.length, 1, "Exactly one unambiguous owner-shadow color required");
  const colorIndex = colorIndices[0]; assert.ok(colorIndex === 0 || colorIndex === 4, "Known owner color must precede or follow four lengths");
  const lengths = tokens.filter((_, index) => index !== colorIndex).map((token, index) => {
    const match = /^([+-]?(?:\d+(?:\.\d*)?|\.\d+))(px)?$/i.exec(token);
    assert.ok(match, "Only finite px lengths or unitless zero offsets are admitted");
    const value = Number(match[1]); assert.ok(Number.isFinite(value));
    assert.ok(match[2] || index < 2 && value === 0, "Nonzero/unitless blur or spread is not an owner-shadow length");
    return value;
  });
  assert.equal(lengths.length, 4); assert.ok(lengths[2] >= 0, "Blur cannot be negative");
  return lengths;
}

test("actual original and corrected layout shadows counter-scale while frozen CSSOM-only control fails", { timeout: 120_000 }, async (t) => {
  const authority = admit(); // No Vite/React/browser import or output allocation before admission.
  const parent = `.gate/${authority.actual.target}/motion-layout-shadow`;
  // Wrapper-owned roots retain their native mode; admission still proves their
  // canonical path, regular ancestry, owner and mirror device.
  for (const relative of [".gate", `.gate/${authority.actual.target}`]) {
    const stat = fs.lstatSync(authority.regular(relative, true)); assert.equal(stat.uid, authority.uid);
  }
  // Only this regression's owned namespaces/cases require private write access.
  for (const relative of [parent, parent + "/runs"]) {
    const file = path.join(authority.root, relative);
    if (!fs.existsSync(file)) fs.mkdirSync(file, { mode: 0o700 });
    const stat = fs.lstatSync(authority.regular(relative, true)); assert.equal(stat.uid, authority.uid); assert.equal(stat.mode & 0o022, 0);
  }
  const relative = `${parent}/runs/run-${randomUUID()}`, directory = path.join(authority.root, relative);
  fs.mkdirSync(directory, { mode: 0o700 }); // Exclusive, retained forever; no recursive reuse or cleanup.
  const write = (name, value) => {
    const file = path.join(directory, name); fs.mkdirSync(path.dirname(file), { recursive: true, mode: 0o700 });
    fs.writeFileSync(file, typeof value === "string" || Buffer.isBuffer(value) ? value : JSON.stringify(value, null, 2) + "\n", { flag: "wx", mode: 0o600 });
  };
  const logs = { build: [], browser: [], errors: [], requests: [] };
  const report = { schema: 1, status: "running", scope: authority.scope, graph_profile: authority.graphProfile, runtime_packages: authority.packages, actual_primary: authority.actual, runtime: authority.versions,
    execution: { node: process.version, executable: process.execPath, argv: process.argv, execArgv: process.execArgv, cwd: process.cwd(), started: new Date().toISOString(),
      caller_streams: "Actual hook.run Node stdout/stderr and command receipt are available after this process returns; preserve the complete primary target beside this case." },
    cases: [], csp: { policy: CSP }, qualified_device: false, production_or_gameplay_qualified: false, automatic_fresh_survival: "UNSET" };
  let browser, server;
  const failures = [];
  try {
    report.parser_controls = [];
    for (const [raw, equivalent, expected] of [
      ["0 0 18px -6px #54e39d", "rgb(84, 227, 157) 0px 0px 18px -6px", [0, 0, 18, -6]],
      ["-0 +0.0 22px -10px #f4a259", "rgb(244, 162, 89) 0px 0px 22px -10px", [-0, 0, 22, -10]],
    ]) {
      const values = shadow(raw), pxValues = shadow(equivalent);
      assert.deepEqual(values.map((value) => value === 0 ? 0 : value), expected.map((value) => value === 0 ? 0 : value));
      assert.deepEqual(values.map((value) => value === 0 ? 0 : value), pxValues);
      report.parser_controls.push({ raw, equivalent, actual: values, expected, status: "pass" });
    }
    for (const invalid of ["1 0 18px -6px #54e39d", "0 2 18px -6px #54e39d", "0 0 18 -6px #54e39d",
      "0 0 18px -6 #54e39d", "0 0 18em -6px #54e39d", "0 0 NaNpx -6px #54e39d", "0 0 Infinitypx -6px #54e39d",
      "inset 0 0 18px -6px #54e39d", "0 0 18px -6px #54e39d, 0 0 2px 1px #fff", "0 0 18px #54e39d",
      "0 0 -18px -6px #54e39d", "0 0 18px -6px #54e39d junk", "0 0 calc(18px) -6px #54e39d"]) {
      assert.throws(() => shadow(invalid)); report.parser_controls.push({ invalid, status: "refused" });
    }
    for (const [name, bytes] of authority.inputs) write("inputs/" + name, bytes);
    const { build } = await import("vite"), { default: react } = await import("@vitejs/plugin-react"), { chromium } = await import("@playwright/test");
    const log = (level) => (message) => { logs.build.push({ level, time: new Date().toISOString(), message }); };
    const result = await build({
      configFile: false, root: authority.regular("frontend/testdata/motion-layout-shadow", true), base: "./", plugins: [react()],
      customLogger: { hasWarned: false, info: log("info"), warn: log("warn"), warnOnce: log("warn"), error: log("error"), clearScreen() {}, hasErrorLogged() { return logs.build.some((entry) => entry.level === "error"); } },
      build: { outDir: path.join(directory, "dist"), emptyOutDir: false, manifest: true, sourcemap: true },
    });
    const outputs = (Array.isArray(result) ? result : [result]).flatMap((item) => item.output ?? []);
    assert.ok(outputs.some((item) => item.type === "chunk" && item.isEntry));
    report.build = { config_file: false, private_root: "frontend/testdata/motion-layout-shadow", output: relative + "/dist", emitted_files: outputs.map((item) => item.fileName) };
    server = createServer((request, response) => {
      const url = new URL(request.url, "http://127.0.0.1"), pathname = decodeURIComponent(url.pathname);
      logs.requests.push({ method: request.method, path: pathname, time: new Date().toISOString() });
      response.setHeader("Content-Security-Policy", CSP); response.setHeader("Cache-Control", "no-store"); response.setHeader("X-Content-Type-Options", "nosniff");
      if (!["GET", "HEAD"].includes(request.method) || pathname.includes("\\") || pathname.split("/").includes("..")) { response.writeHead(400); response.end(); return; }
      const file = path.join(directory, "dist", pathname === "/" ? "index.html" : pathname.slice(1));
      if (!file.startsWith(path.join(directory, "dist") + path.sep) || !fs.existsSync(file) || !fs.lstatSync(file).isFile() || fs.lstatSync(file).isSymbolicLink()) { response.writeHead(404); response.end(); return; }
      const type = { ".html": "text/html; charset=utf-8", ".js": "text/javascript; charset=utf-8", ".css": "text/css; charset=utf-8", ".woff2": "font/woff2", ".json": "application/json", ".map": "application/json" }[path.extname(file)];
      response.setHeader("Content-Type", type || "application/octet-stream"); response.writeHead(200); response.end(request.method === "HEAD" ? undefined : fs.readFileSync(file));
    });
    await new Promise((resolve, reject) => { server.once("error", reject); server.listen(0, "127.0.0.1", resolve); });
    const origin = `http://127.0.0.1:${server.address().port}`; report.server = { origin, scope: "private loopback static fixture only" };
    browser = await chromium.launch({ headless: true }); report.browser_version = browser.version();
    for (const [owner, blur, spread] of [["conexiuni", 18, -6], ["caldrece", 22, -10]]) {
      const page = await browser.newPage({ viewport: { width: 1280, height: 900 }, reducedMotion: "no-preference", locale: "ro-RO", timezoneId: "Europe/Bucharest" });
      page.on("console", (message) => logs.browser.push({ owner, type: message.type(), text: message.text() }));
      page.on("pageerror", (error) => logs.errors.push({ owner, message: error.message, stack: error.stack }));
      await page.addInitScript(() => { globalThis.__motionCspViolations = []; globalThis.document.addEventListener("securitypolicyviolation", (event) => globalThis.__motionCspViolations.push({ effectiveDirective: event.effectiveDirective, blockedURI: event.blockedURI, disposition: event.disposition })); });
      const response = await page.goto(`${origin}/?owner=${owner}`); assert.equal(response.status(), 200); assert.equal(response.headers()["content-security-policy"], CSP);
      await page.evaluate(() => globalThis.document.fonts.ready);
      const selector = `[data-owner="${owner}"][data-variant]`;
      const waitSettled = () => page.evaluate(async (query) => {
        const lens = globalThis.__motionLayoutShadow, deadline = globalThis.performance.now() + 15_000;
        let consecutive = 0, previous = null;
        const samples = [];
        while (globalThis.performance.now() < deadline) {
          await new Promise((resolve) => globalThis.requestAnimationFrame(resolve));
          const rows = [...globalThis.document.querySelectorAll(query)].map((element) => {
            const css = globalThis.getComputedStyle(element), rect = element.getBoundingClientRect(), observed = lens.inspect(element);
            return { variant: element.dataset.variant, connected: element.isConnected, width: rect.width, height: rect.height,
              sx: rect.width / element.offsetWidth, sy: rect.height / element.offsetHeight,
              opacity: Number(css.opacity), latestScale: observed.latestScale,
              animationComplete: lens.events.some((event) => event.variant === element.dataset.variant && event.event === "animation-complete") };
          });
          samples.push({ time: globalThis.performance.now(), rows });
          const identity = rows.length === 3 && rows.every((row) => row.connected && row.animationComplete
            && Math.abs(row.opacity - 1) < 0.001 && Math.abs(row.sx - 1) < 0.002 && Math.abs(row.sy - 1) < 0.002
            && row.latestScale !== null && Math.abs(row.latestScale - 1) < 0.0001);
          const stable = previous && rows.every((row, index) => row.variant === previous[index]?.variant
            && Math.abs(row.width - previous[index].width) < 0.02 && Math.abs(row.height - previous[index].height) < 0.02
            && Math.abs(row.opacity - previous[index].opacity) < 0.0001);
          consecutive = identity && stable ? consecutive + 1 : 0;
          if (consecutive >= 10) return { consecutive, samples };
          previous = rows;
        }
        throw new Error("Actual entrance/layout did not settle for ten consecutive RAF samples: " + JSON.stringify(samples.slice(-12)));
      }, selector);
      const initialSettling = await waitSettled();
      const sample = (phase, change) => page.evaluate(async ({ query, phase, change }) => {
        const lens = globalThis.__motionLayoutShadow, frames = [];
        if (!lens || lens.feature !== "domMax") throw Error("Actual domMax fixture lens required");
        const before = lens.events.length;
        if (change) globalThis.document.getElementById(change).click();
        for (let frame = 0; frame < (change === "toggle-size" ? 80 : 1); frame++) {
          await new Promise((resolve) => globalThis.requestAnimationFrame(resolve));
          frames.push({ time: globalThis.performance.now(), rows: [...globalThis.document.querySelectorAll(query)].map((element) => {
            const css = globalThis.getComputedStyle(element), rect = element.getBoundingClientRect(), matrix = new globalThis.DOMMatrixReadOnly(css.transform === "none" ? undefined : css.transform);
            return { variant: element.dataset.variant, active: element.dataset.active, large: element.dataset.large, connected: element.isConnected,
              width: rect.width, height: rect.height, layoutWidth: element.offsetWidth, layoutHeight: element.offsetHeight,
              sx: rect.width / element.offsetWidth, sy: rect.height / element.offsetHeight, transform: css.transform, matrix: [matrix.a, matrix.b, matrix.c, matrix.d, matrix.e, matrix.f],
              shadow: css.boxShadow, inlineShadow: element.style.boxShadow, opacity: Number(css.opacity), projection: lens.inspect(element) };
          }) });
        }
        return { phase, frames, events: lens.events.slice(before), feature: lens.feature };
      }, { query: selector, phase, change });
      const record = { owner, base_blur: blur, base_spread: spread, initial_settling: initialSettling, later_settling: [], phases: [], outcomes: {}, headers: response.headers() };
      report.cases.push(record);
      const initial = await sample("initial", null); record.phases.push(initial);
      for (const row of initial.frames[0].rows) { assert.ok(row.connected && row.projection.projection); assert.equal(shadow(row.shadow)[2], blur); assert.equal(shadow(row.shadow)[3], spread); }
      for (const phase of ["grow", "shrink"]) {
        const observed = await sample(phase, "toggle-size"); record.phases.push(observed);
        for (const variant of variants) {
          assert.ok(observed.events.some((event) => event.variant === variant && event.event === "layout-start"), `${owner}/${variant} actual projection event required`);
          const admitted = observed.frames.flatMap((frame) => frame.rows.filter((row) => row.variant === variant && row.connected && row.projection.projection
            && Math.abs(row.matrix[1]) < 0.001 && Math.abs(row.matrix[2]) < 0.001 && Math.abs(row.sx - row.sy) < 0.015
            && (phase === "grow" ? row.sx > 0.6 && row.sx < 0.85 : row.sx > 1.2 && row.sx < 1.7)));
          assert.ok(admitted.length >= 2, `${owner}/${phase}/${variant} real nonidentity layout frames required`);
          for (const row of admitted) {
            assert.ok(Number.isFinite(row.projection.projectionScaleX) && Number.isFinite(row.projection.treeScaleX));
            assert.ok(Number.isFinite(row.projection.projectionScaleY) && Number.isFinite(row.projection.treeScaleY));
            assert.ok(Math.abs(row.sx - row.projection.projectionScaleX * row.projection.treeScaleX) < 0.025);
            assert.ok(Math.abs(row.sy - row.projection.projectionScaleY * row.projection.treeScaleY) < 0.025);
            if (variant === "broken-cssom") assert.equal(row.projection.latestShadow, null);
            else { assert.equal(shadow(row.projection.latestShadow)[2], blur); assert.equal(shadow(row.projection.latestShadow)[3], spread); }
          }
          const checks = admitted.map((row) => {
            const lengths = shadow(row.shadow), scale = (row.sx + row.sy) / 2;
            return { scale, blur: lengths[2], spread: lengths[3], visual_blur: lengths[2] * scale, visual_spread: lengths[3] * scale,
              contract: Math.abs(lengths[2] * scale - blur) < 0.6 && Math.abs(lengths[3] * scale - spread) < 0.35 };
          });
          record.outcomes[`${phase}/${variant}`] = { actual_admitted_frames: admitted.length, checks, contract_passed: checks.every((item) => item.contract) };
          if (variant === "broken-cssom") {
            assert.ok(checks.every((item) => !item.contract), "Negative control must actually violate the identical visual invariant");
            assert.ok(checks.every((item) => Math.abs(item.blur - blur) < 0.2 && Math.abs(item.spread - spread) < 0.2));
          } else assert.ok(checks.every((item) => item.contract), `${owner}/${phase}/${variant} actual counter-scale correction required`);
        }
        record.later_settling.push(await waitSettled()); await page.screenshot({ path: path.join(directory, `${owner}-${phase}-settled.png`) });
      }
      await page.locator("#toggle-active").click(); record.later_settling.push(await waitSettled());
      const removed = await sample("selected/latest-to-undefined", null); record.phases.push(removed);
      const rows = removed.frames[0].rows, original = rows.find((row) => row.variant === "original");
      assert.equal(original.active, "false");
      for (const row of rows) assert.equal(row.active, "false");
      const corrected = rows.find((row) => row.variant === "corrected");
      assert.equal(corrected.shadow, original.shadow, "Corrected removal must retain actual original semantics, not invent a fallback");
      assert.equal(corrected.inlineShadow, original.inlineShadow);
      assert.equal(corrected.projection.latestShadow, original.projection.latestShadow);
      // Broken CSSOM remains the mandatory scaling-negative arm. Its removal
      // difference is retained as observed evidence, not positive equivalence.
      record.outcomes.removal = { original: original.shadow, corrected: corrected.shadow,
        broken_cssom: rows.find((row) => row.variant === "broken-cssom").shadow, positive_equivalent: true };
      await page.locator("#toggle-active").click(); record.later_settling.push(await waitSettled());
      const restored = await sample("restored", null); record.phases.push(restored);
      for (const row of restored.frames[0].rows) { assert.equal(row.active, "true"); assert.equal(shadow(row.shadow)[2], blur); assert.equal(shadow(row.shadow)[3], spread); }
      const restoredOriginal = restored.frames[0].rows.find((row) => row.variant === "original");
      const restoredCorrected = restored.frames[0].rows.find((row) => row.variant === "corrected");
      assert.equal(restoredCorrected.shadow, restoredOriginal.shadow); assert.equal(restoredCorrected.inlineShadow, restoredOriginal.inlineShadow);
      assert.equal(restoredCorrected.projection.latestShadow, restoredOriginal.projection.latestShadow);
      record.csp = await page.evaluate(() => globalThis.__motionCspViolations); assert.deepEqual(record.csp, []);
      assert.ok(logs.errors.length === 0); await page.screenshot({ path: path.join(directory, `${owner}-restored.png`) }); await page.close();
    }
    report.guard_rejections = [];
    for (const [kind, expected] of [
      ["raw-style", "Use explicit CSSOM declarations"],
      ["getter", "CSS declarations must use own data properties: boxShadow"],
      ["numeric-shadow", "CSS length requires explicit units: boxShadow"],
      ["layout-radius", "Unreviewed Motion layout CSS ownership: borderRadius"],
    ]) {
      const record = { kind, expected, url: `${origin}/?owner=conexiuni&guard=${kind}`, outcome: null,
        actual_console: [], actual_errors: [], actual_csp: [], browser_csp_snapshot: null, applied_probe_nodes: null };
      report.guard_rejections.push(record); // Keep identity/live evidence even if navigation or marker fails.
      const page = await browser.newPage({ reducedMotion: "no-preference" });
      page.on("console", (message) => record.actual_console.push({ type: message.type(), text: message.text() }));
      page.on("pageerror", (error) => record.actual_errors.push({ message: error.message, stack: error.stack }));
      await page.exposeFunction("__recordMotionGuardCsp", (event) => record.actual_csp.push(event));
      await page.addInitScript(() => {
        globalThis.__motionGuardCsp = [];
        globalThis.__motionGuardApplied = [];
        new MutationObserver((records) => {
          for (const record of records) for (const node of record.addedNodes) {
            if (node.nodeType !== Node.ELEMENT_NODE) continue;
            const probes = [node, ...node.querySelectorAll("[data-guard-probe]")].filter((element) => element.hasAttribute("data-guard-probe"));
            for (const probe of probes) globalThis.__motionGuardApplied.push({ kind: probe.dataset.guardProbe, style: probe.getAttribute("style") });
          }
        }).observe(globalThis.document, { childList: true, subtree: true });
        globalThis.document.addEventListener("securitypolicyviolation", (event) => {
          const observed = { effectiveDirective: event.effectiveDirective, blockedURI: event.blockedURI, disposition: event.disposition };
          globalThis.__motionGuardCsp.push(observed); void globalThis.__recordMotionGuardCsp(observed);
        });
      });
      const response = await page.goto(record.url);
      assert.equal(response.status(), 200); assert.equal(response.headers()["content-security-policy"], CSP);
      await page.locator("#guard-outcome").waitFor();
      record.outcome = await page.locator("#guard-outcome").evaluate((element) => ({ error: element.dataset.error, reads: Number(element.dataset.reads) }));
      record.browser_csp_snapshot = await page.evaluate(async () => {
        await new Promise((resolve) => globalThis.requestAnimationFrame(() => globalThis.requestAnimationFrame(resolve)));
        return globalThis.__motionGuardCsp;
      });
      record.applied_probe_nodes = await page.evaluate(() => globalThis.__motionGuardApplied);
      assert.equal(record.outcome.error, expected); assert.equal(record.outcome.reads, 0);
      assert.deepEqual(record.actual_csp, []); assert.deepEqual(record.browser_csp_snapshot, []);
      assert.deepEqual(record.applied_probe_nodes, [], "Guard must refuse before an unsafe probe reaches the DOM");
      await page.close();
    }
    for (const [file, bytes] of authority.inputs) assert.deepEqual(authority.read(file), bytes, "Execution source or bootstrap input changed");
    assert.ok(logs.requests.every((request) => !request.path.startsWith("/api/"))); report.status = "pass";
  } catch (error) { report.status = "fail"; report.error = { message: error.message, stack: error.stack }; failures.push(error); }
  finally {
    try { if (browser) await browser.close(); }
    catch (error) { failures.push(error); report.status = "fail"; report.browser_close_error = error.message; }
    try { if (server) await new Promise((resolve, reject) => server.close((error) => error ? reject(error) : resolve())); }
    catch (error) { failures.push(error); report.status = "fail"; report.server_close_error = error.message; }
    report.execution.finished = new Date().toISOString();
    report.source_inputs = [...authority.inputs].map(([file, bytes]) => ({ path: file, bytes: bytes.length, sha256: hash(bytes) }));
    try {
      write("observations.json", report.cases); write("runtime-and-sources.json", { actual_primary: report.actual_primary, runtime: report.runtime, source_inputs: report.source_inputs, execution: report.execution });
      write("build.log.json", logs.build); write("browser-console.log.json", logs.browser); write("browser-errors.log.json", logs.errors); write("server-requests.log.json", logs.requests); write("report.json", report);
    } catch (error) { failures.push(error); report.status = "fail"; report.retention_error = error.message; }
    try { t.diagnostic(`Retain complete actual case ${directory}, built dist, source inputs, observations and actual ROOT ${authority.root}/${report.actual_primary.target} command/config/bootstrap streams before every fresh/reset. No automatic physical survival is claimed.`); }
    catch (error) { failures.push(error); }
  }
  if (failures.length === 1) throw failures[0];
  if (failures.length > 1) throw new AggregateError(failures, "Motion execution or cleanup failed", { cause: failures[0] });
});
