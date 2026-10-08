import assert from "node:assert/strict";
import { createRequire } from "node:module";
import { randomUUID } from "node:crypto";
import * as fs from "node:fs";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";
import { rolldown } from "rolldown";
import {
  SDK_ALLOCATION_BINDING, SDK_UNUSED_ALLOCATIONS, allocationHash,
  annotateUnusedSdkAllocations, assertSdkAllocationBinding, boundSdkAllocationInputs,
} from "./gui-sdk-allocation-plugin.mts";

const frontend = fs.realpathSync(fileURLToPath(new URL("../", import.meta.url)));
const root = path.dirname(frontend);
assert.equal(process.cwd(), frontend, "Run the allocation audit from its owning frontend package");
assert.equal(process.env.NODE_ENV, "production", "Allocation audit requires actual production React selection");
const context = JSON.parse(fs.readFileSync(path.join(root, ".gate/wrapper-current.json")));
assert.equal(context.target, "gen");
assert.equal(context.sha, process.env.GATE_SHA);
assert.equal(context.tree_sha256, process.env.GATE_TREE_SHA256);
assert.equal(context.toolchain_digest, process.env.TOOLCHAIN_DIGEST);
const relative = `.gate/gen/normalized-react/sdk-allocation-audit/run-${randomUUID()}`;
const directory = path.join(root, relative);
fs.mkdirSync(directory, { recursive: true, mode: 0o700 });
const artifacts = [], observations = {};
function retain(name, bytes) {
  fs.writeFileSync(path.join(directory, name), bytes, { flag: "wx", mode: 0o600 });
  const digest = allocationHash(bytes);
  artifacts.push(`${relative}/${name} sha256:${digest}`);
  return { path: `${relative}/${name}`, sha256: digest, bytes: Buffer.byteLength(bytes) };
}
let failure;
try {
  const inputs = boundSdkAllocationInputs(frontend);
  const annotated = annotateUnusedSdkAllocations(inputs.uiSource);
  let restored = annotated;
  for (const { binding } of SDK_UNUSED_ALLOCATIONS) {
    restored = restored.replace(`, ${binding} = /* @__PURE__ */ m(function(`, `, ${binding} = m(function(`);
  }
  assert.equal(restored, inputs.uiSource, "Annotation removal must restore every original byte");
  assert.throws(() => annotateUnusedSdkAllocations(inputs.uiSource + "\n"), /payload differs/);
  assert.throws(() => annotateUnusedSdkAllocations(annotated), /payload differs/);
  assert.throws(() => assertSdkAllocationBinding({ ...SDK_ALLOCATION_BINDING, uiVersion: "1.0.2" }), /binding differs/);
  assert.throws(() => assertSdkAllocationBinding({ ...SDK_ALLOCATION_BINDING, reactProductionSha256: "0".repeat(64) }), /binding differs/);
  observations.tamper_refusals = 4;
  observations.source = { before: retain("sdk-original.js", inputs.uiSource),
    after: retain("sdk-annotated.js", annotated), comments_only_restoration: true };
  const require = createRequire(path.join(frontend, "package.json"));
  const react = require(inputs.reactProductionPath);
  let renders = 0;
  const render = () => { renders++; };
  const probe = react.forwardRef(render);
  assert.equal(renders, 0);
  assert.equal(probe.render, render);
  assert.equal(probe.$$typeof, Symbol.for("react.forward_ref"));
  assert.deepEqual(Object.keys(probe).sort(), ["$$typeof", "render"]);
  observations.production_forward_ref = { renderer_invocations: renders,
    renderer_identity_preserved: true, own_keys: Object.keys(probe).sort(),
    source: retain("react-production.cjs", inputs.reactProductionSource) };
  observations.packages = inputs.packages.map((pkg) => ({ name: pkg.name, version: pkg.version,
    manifest: retain(`${pkg.name.replaceAll("/", "-").replaceAll("@", "")}-package.json`, fs.readFileSync(pkg.manifestPath)) }));
  const rolldownPath = path.join(frontend, "node_modules/rolldown/package.json");
  const rolldownBytes = fs.readFileSync(rolldownPath), rolldownPackage = JSON.parse(rolldownBytes);
  const lock = JSON.parse(fs.readFileSync(path.join(frontend, "package-lock.json")));
  assert.equal(rolldownPackage.name, "rolldown");
  assert.equal(rolldownPackage.version, lock.packages["node_modules/rolldown"].version);
  assert.equal(fs.realpathSync(path.dirname(rolldownPath)), path.dirname(rolldownPath));
  observations.rolldown = { version: rolldownPackage.version, manifest: retain("rolldown-package.json", rolldownBytes) };
  const jsxPath = path.join(frontend, "node_modules/react/cjs/react-jsx-runtime.production.js");
  assert.equal(fs.realpathSync(jsxPath), jsxPath);
  observations.production_jsx_runtime = retain("react-jsx-production.cjs", fs.readFileSync(jsxPath));
  const tracerPath = path.join(directory, "react-allocation-tracer.mjs");
  // This audit-owned observer forwards every operation to the bound production
  // React implementation; it never replaces renderer bodies or SDK exports.
  const tracerSource = `import React from ${JSON.stringify(inputs.reactProductionPath)};\n`
    + `export * from ${JSON.stringify(inputs.reactProductionPath)};\n`
    + "export const allocations = [];\nexport function forwardRef(render) {\n"
    + "  const result = React.forwardRef(render);\n"
    + "  allocations.push({ source: render.toString(), renderer_identity_preserved: result.render === render });\n"
    + "  return result;\n}\n";
  observations.tracer = retain("react-allocation-tracer.mjs", tracerSource);
  const entry = "\0cat-sdk-allocation-audit-entry", sourceId = "\0cat-sdk-allocation-audit-source";
  const bundles = {};
  for (const [label, source] of [["before", inputs.uiSource], ["after", annotated]]) {
    const logs = [];
    const bundle = await rolldown({ input: entry, onLog(level, log) { logs.push({ level, message: log.message }); },
      plugins: [{ name: "cat-sdk-allocation-audit-input", resolveId(id) {
        if (id === entry || id === sourceId) return id;
        if (id === "react") return { id: tracerPath, external: true };
        if (id === "react/jsx-runtime") return { id: jsxPath, external: true };
        return null;
      }, load(id) {
        if (id === entry) return `export { Button, Badge, ThemeProvider, ToastStack } from ${JSON.stringify(sourceId)};`;
        if (id === sourceId) return source;
        return null;
      } }],
    });
    try {
      const generated = await bundle.generate({ format: "es", minify: false });
      assert.equal(generated.output.length, 1, "Isolated allocation bundle must be one actual chunk");
      assert.equal(generated.output[0].type, "chunk");
      assert.equal(logs.length, 0, "Isolated allocation bundle emitted diagnostics");
      bundles[label] = { code: generated.output[0].code,
        output: retain(`${label}.mjs`, generated.output[0].code), logs: retain(`${label}.logs.json`, JSON.stringify(logs) + "\n") };
    } finally { await bundle.close(); }
  }
  const tracer = await import(pathToFileURL(tracerPath).href);
  const exportsByLabel = {}, traces = {};
  for (const label of ["before", "after"]) {
    tracer.allocations.length = 0;
    exportsByLabel[label] = await import(pathToFileURL(path.join(directory, `${label}.mjs`)).href);
    traces[label] = tracer.allocations.map((item) => ({ ...item }));
    retain(`${label}.allocations.json`, JSON.stringify(traces[label], null, 2) + "\n");
    assert.deepEqual(Object.keys(exportsByLabel[label]).sort(), ["Badge", "Button", "ThemeProvider", "ToastStack"]);
    assert.ok(traces[label].every((item) => item.renderer_identity_preserved));
  }
  assert.equal(traces.before.length, 5, "Control must execute Button plus all four unused allocations");
  assert.equal(traces.after.length, 1, "Annotated bundle must execute only the used Button allocation");
  for (const { component, marker } of SDK_UNUSED_ALLOCATIONS) {
    assert.equal(traces.before.filter((item) => item.source.includes(marker)).length, 1, `${component} control allocation missing`);
    assert.ok(bundles.before.code.includes(marker));
    assert.ok(!bundles.after.code.includes(marker), `${component} callback survived unused allocation removal`);
  }
  assert.ok(traces.after[0].source.includes("roedu-btn"));
  assert.equal(traces.before[0].source, traces.after[0].source, "Used Button renderer body changed");
  const usedBodies = {};
  for (const name of ["Badge", "ThemeProvider", "ToastStack"]) {
    assert.equal(typeof exportsByLabel.before[name], "function");
    assert.equal(exportsByLabel.before[name].toString(), exportsByLabel.after[name].toString(), `${name} body changed`);
    usedBodies[name] = allocationHash(exportsByLabel.after[name].toString());
  }
  const ref = { current: null }, onClick = () => {};
  const props = { variant: "secondary", size: "sm", block: true, type: "submit",
    className: "allocation-audit", disabled: true, children: "Allocation audit", onClick };
  const originalButton = exportsByLabel.before.Button.render(props, ref);
  const annotatedButton = exportsByLabel.after.Button.render(props, ref);
  assert.deepEqual(originalButton, annotatedButton, "Used Button output/ref/callback differs");
  assert.equal(annotatedButton.type, "button");
  assert.equal(annotatedButton.props.ref, ref);
  assert.equal(annotatedButton.props.onClick, onClick);
  observations.causality = { control_allocations: traces.before.length, annotated_allocations: traces.after.length,
    removed: SDK_UNUSED_ALLOCATIONS.map(({ component }) => component), retained: ["Button", ...Object.keys(usedBodies)],
    button_renderer_sha256: allocationHash(traces.after[0].source), used_body_sha256: usedBodies,
    button_output_ref_and_callback_equal: true, before_bundle: bundles.before.output, after_bundle: bundles.after.output };
} catch (error) {
  failure = error instanceof Error ? error.message : String(error);
}
const report = { schema: 1, check: "cat-sdk-allocation-causality", status: failure ? "fail" : "pass",
  scope: "isolated actual Rolldown bundles and bound production React allocations",
  application_qualified: false, startup_budget_qualified: false, full_game_replay_qualified: false,
  sha: context.sha, tree_sha256: context.tree_sha256, toolchain_digest: context.toolchain_digest,
  invocation: context.invocation, observations, ...(failure ? { failure } : {}), artifacts };
fs.writeFileSync(path.join(directory, "report.json"), JSON.stringify(report, null, 2) + "\n", { flag: "wx", mode: 0o600 });
process.stdout.write(JSON.stringify(report) + "\n");
process.exitCode = failure ? 1 : 0;
