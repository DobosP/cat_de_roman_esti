// Finite consumer preflight. Commands execute only through the owning GEN hook.
// Formatting is diagnostic: actual stdout is retained; source is never rewritten.
import * as fs from "node:fs";
import path from "node:path";
import { createHash } from "node:crypto";

const module = "github.com/DobosP/cat_de_roman_esti/go-backend";
const selected = {
  "internal/guibuild": [
    "TestLoadBindsExactEmbeddedBytes",
    "TestLoadRejectsMissingInputs",
    "TestLoadRejectsMalformedDescriptor",
    "TestLoadRejectsInvalidOrMismatchedBindings",
    "TestLoadRejectsNonObjectJSONInputs",
    "TestLoadRejectsOversizedAndNonRegularInputs",
    "TestLoadIgnoresRuntimeEnvironmentClaims",
    "TestGenerateCopiesExactLockBytesAndExplicitSourceBinding",
    "TestGenerateFailureRemovesEarlierDescriptor",
    "TestGenerateRejectsSymlinkedInputsAndClearsEarlierDescriptor",
    "TestGenerateRejectsSymlinkedOutputAncestorWithoutOutsideWrites",
    "TestGenerateRejectsNonRegularInputAndClearsEarlierDescriptor",
    "TestGenerateRejectsSymlinkedDescriptorWithoutRemovingOutsideFile",
    "TestGenerateRejectsRootAliasWithoutOutsideWrites",
  ],
  "internal/httpapi": [
    "TestManagedNonceShellBytePreservationAndSDKContext",
    "TestManagedNonceShellRefusals",
    "TestManagedNonceResponseFreshnessAndStages",
    "TestManagedNonceLegacyAndInvalidFlag",
    "TestManagedCSPReportReceiverBoundsWithoutPersistence",
    "TestManagedNonceCanceledContextAndRequestRefuseHTML",
    "TestManagedNonceRenderAndSDKRefusalsAreNoStore",
    "TestGUIBuildEndpointUsesExactCompiledBinding",
    "TestGUIBuildEndpointUnavailableBindings",
    "TestGUIBuildEndpointRejectsLegacyAndDiskOverride",
    "TestGUIBuildEndpointIgnoresSpoofedRuntimeIdentity",
    "TestGUIBuildPrivateFilesAndHealthRemainBounded",
    "TestGUIKitAssetsManifestNonceContract",
    "TestManagedSPANonHexViteCacheUsesActualSDKStatus",
  ],
  "cmd/cat-server": ["TestGUIHealthcheckRejectsUnsupportedInvocation"],
};
const formatFiles = [
  "go-backend/cmd/cat-gui-build/main.go",
  "go-backend/cmd/cat-server/main.go",
  "go-backend/cmd/cat-server/main_test.go",
  "go-backend/cmd/cat-server/gui_health.go",
  "go-backend/cmd/cat-server/gui_health_test.go",
  "go-backend/embedfs/assets.go",
  "go-backend/internal/guibuild/identity.go",
  "go-backend/internal/guibuild/identity_test.go",
  "go-backend/internal/guibuild/generate.go",
  "go-backend/internal/guibuild/generate_test.go",
  "go-backend/internal/httpapi/server.go",
  "go-backend/internal/httpapi/website.go",
  "go-backend/internal/httpapi/website_test.go",
  "go-backend/internal/httpapi/managed_spa.go",
  "go-backend/internal/httpapi/managed_spa_test.go",
  "go-backend/internal/httpapi/managed_nonce.go",
  "go-backend/internal/httpapi/managed_nonce_test.go",
  "go-backend/internal/httpapi/gui_build.go",
  "go-backend/internal/httpapi/gui_build_test.go",
  "go-backend/internal/httpapi/gui_kit_assets_contract_test.go",
];
const hash = (bytes) => createHash("sha256").update(bytes).digest("hex");
function confined(root, relative, missing = false) {
  if (!relative || relative.startsWith("/") || /[\\:\x00-\x1f\x7f]/.test(relative)
    || relative.split("/").some((part) => !part || part === "." || part === "..")) throw Error("Unsafe native preflight path");
  let cursor = root;
  for (const part of relative.split("/")) {
    cursor = path.join(cursor, part);
    let stat;
    try { stat = fs.lstatSync(cursor); }
    catch (error) { if (missing && error.code === "ENOENT") continue; throw error; }
    if (stat.isSymbolicLink() || (!stat.isDirectory() && !stat.isFile())) throw Error("Nonregular native preflight path");
  }
  return cursor;
}
function admit(hook) {
  hook.assert("Actual owning Linux GEN context", () => {
    const ctx = hook.context;
    if (process.platform !== "linux" || process.cwd() !== "/work" || ctx.root !== "/work" || ctx.target !== "gen") return false;
    const read = (relative) => fs.readFileSync(confined(ctx.root, relative));
    const own = (value, fields) => value && typeof value === "object" && !Array.isArray(value)
      && Object.keys(value).length === fields.length && fields.every((field) => Object.hasOwn(value, field));
    const uuid = /^[a-f0-9]{8}-[a-f0-9]{4}-4[a-f0-9]{3}-[89ab][a-f0-9]{3}-[a-f0-9]{12}$/;
    const hex = /^[a-f0-9]{64}$/;
    const descriptorBytes = read(".gate/wrapper-current.json"), current = JSON.parse(descriptorBytes);
    if (!own(current, ["schema", "invocation", "target", "sha", "tree_sha256", "toolchain_digest", "config_sha256", "config_path", "config_file_sha256"])
      || current.schema !== 1 || current.target !== "gen" || !uuid.test(current.invocation) || !uuid.test(ctx.invocation)
      || current.sha !== ctx.sha || current.sha !== process.env.GATE_SHA
      || current.tree_sha256 !== ctx.tree_sha256 || current.tree_sha256 !== process.env.GATE_TREE_SHA256
      || current.toolchain_digest !== ctx.toolchain_digest || current.toolchain_digest !== process.env.TOOLCHAIN_DIGEST
      || current.config_path !== ".gate/gen/wrapper-kit-config.json" || !hex.test(current.config_sha256)
      || !hex.test(current.config_file_sha256) || !read(".gate/gen/wrapper-current.json").equals(descriptorBytes)) return false;
    const capturedBytes = read(current.config_path), captured = JSON.parse(capturedBytes);
    if (hash(capturedBytes) !== current.config_file_sha256
      || !own(captured, ["schema", "target", "sha", "tree_sha256", "toolchain_digest", "config", "config_sha256", "command"])
      || ["schema", "target", "sha", "tree_sha256", "toolchain_digest", "config_sha256"].some((key) => captured[key] !== current[key])
      || captured.config?.role !== "consumer" || captured.config.app !== "cat_de_roman_esti"
      || hash(JSON.stringify(captured.config)) !== current.config_sha256
      || !own(captured.command, ["command", "args", "exit_code", "duration_ms", "stdout_sha256", "stderr_sha256"])
      || captured.command.command !== "task" || JSON.stringify(captured.command.args) !== '["--silent","repo:kit-config"]'
      || captured.command.exit_code !== 0 || !Number.isInteger(captured.command.duration_ms) || captured.command.duration_ms < 0
      || !hex.test(captured.command.stdout_sha256) || captured.command.stderr_sha256 !== hash("")) return false;
    const bootstrap = JSON.parse(read(".gate/gen/bootstrap-execution.json"));
    if (!own(bootstrap, ["schema", "target", "invocation", "sha", "tree_sha256", "toolchain_digest", "started", "config", "config_sha256",
      "wrapper_target", "wrapper_config", "wrapper_config_sha256", "wrapper_invocation", "wrapper_descriptor", "wrapper_descriptor_sha256", "actions", "artifacts", "finished"])
      || bootstrap.schema !== 1 || bootstrap.target !== "gen" || bootstrap.invocation !== ctx.invocation
      || ["sha", "tree_sha256", "toolchain_digest"].some((key) => bootstrap[key] !== ctx[key])
      || JSON.stringify(bootstrap.config) !== JSON.stringify(captured.config) || bootstrap.config_sha256 !== current.config_sha256
      || bootstrap.wrapper_target !== "gen" || bootstrap.wrapper_invocation !== current.invocation
      || bootstrap.wrapper_config !== current.config_path || bootstrap.wrapper_config_sha256 !== hash(capturedBytes)
      || bootstrap.wrapper_descriptor !== ".gate/wrapper-current.json" || bootstrap.wrapper_descriptor_sha256 !== hash(descriptorBytes)
      || !Number.isFinite(Date.parse(ctx.started)) || !Number.isFinite(Date.parse(bootstrap.started)) || !Number.isFinite(Date.parse(bootstrap.finished))
      || Date.parse(bootstrap.finished) < Date.parse(bootstrap.started) || Date.parse(bootstrap.finished) > Date.parse(ctx.started)
      || !Array.isArray(bootstrap.actions) || !bootstrap.actions.length || !Array.isArray(bootstrap.artifacts)) return false;
    // The bootstrap links the inner SDK/hook invocation to the distinct primary
    // wrapper invocation. Verify its actual streams rather than equating them.
    const listed = new Map();
    for (const artifact of bootstrap.artifacts) {
      const match = /^(.+) sha256:([a-f0-9]{64})$/.exec(artifact);
      if (!match || listed.has(match[1]) || !match[1].startsWith(`.gate/gen/logs/${ctx.invocation}-bootstrap-`)
        || hash(read(match[1])) !== match[2]) return false;
      listed.set(match[1], match[2]);
    }
    const used = new Set();
    for (const action of bootstrap.actions) {
      if (!own(action, ["phase", "kind", "command", "argument_count", "args_sha256", "cwd", "exit_code", "duration_ms", "stdout_sha256", "stderr_sha256", "stdout_log", "stderr_log"])
        || action.kind !== "command" || action.exit_code !== 0 || action.cwd !== "."
        || typeof action.phase !== "string" || !/^[A-Za-z][A-Za-z0-9._-]*$/.test(action.phase)
        || typeof action.command !== "string" || !action.command || !Number.isInteger(action.argument_count) || action.argument_count < 0
        || !hex.test(action.args_sha256) || !Number.isInteger(action.duration_ms) || action.duration_ms < 0
        || listed.get(action.stdout_log) !== action.stdout_sha256 || listed.get(action.stderr_log) !== action.stderr_sha256
        || used.has(action.stdout_log) || used.has(action.stderr_log)) return false;
      used.add(action.stdout_log); used.add(action.stderr_log);
    }
    return listed.size === bootstrap.actions.length * 2 && used.size === listed.size;
  });
}
function save(hook, relative, bytes) {
  const file = confined(hook.context.root, relative, true);
  fs.mkdirSync(path.dirname(file), { recursive: true });
  fs.writeFileSync(file, bytes);
  hook.artifact(relative);
}
function bound(hook) {
  return { sha: hook.context.sha, tree_sha256: hook.context.tree_sha256,
    invocation: hook.context.invocation, toolchain_digest: process.env.TOOLCHAIN_DIGEST };
}

export function runNativeSourcePreflight(hook) {
  hook.check("cat-native-source-contracts", () => {
    admit(hook);
    const expected = Object.entries(selected).flatMap(([scope, tests]) => tests.map((test) => ({ package: `${module}/${scope}`, test })));
    const names = expected.map(({ test }) => test);
    hook.assert("Exact finite twenty-nine-test selection", () => names.length === 29 && new Set(names).size === 29);
    const args = ["test", "-race", "-json", "-count=1", "-run", `^(${names.join("|")})$`, ...Object.keys(selected).map((scope) => `./${scope}`)];
    let output = "", error, commandFailure;
    try { output = hook.run("go", args, path.join(hook.context.root, "go-backend"), { CGO_ENABLED: "1" }); }
    catch (failure) { output = failure.stdout ?? ""; error = failure.message; commandFailure = failure; }
    const action = hook.actions.findLast((item) => item.kind === "command" && item.check === "cat-native-source-contracts");
    const events = [], malformed = [];
    for (const [index, line] of output.split("\n").entries()) {
      if (!line.trim()) continue;
      try { events.push(JSON.parse(line)); } catch { malformed.push(index + 1); }
    }
    const observed = expected.map((item) => ({ ...item,
      run: events.filter((event) => event.Package === item.package && event.Test === item.test && event.Action === "run").length,
      pass: events.filter((event) => event.Package === item.package && event.Test === item.test && event.Action === "pass").length }));
    const packages = Object.keys(selected).map((scope) => `${module}/${scope}`);
    const packagePasses = packages.map((name) => ({ package: name,
      pass: events.filter((event) => event.Package === name && !event.Test && event.Action === "pass").length }));
    const refused = events.filter((event) => ["skip", "fail"].includes(event.Action));
    const unexpected = events.filter((event) => !packages.includes(event.Package)
      || (event.Test && !expected.some((item) => item.package === event.Package && item.test === event.Test.split("/")[0])));
    const pass = !error && action?.exit_code === 0 && malformed.length === 0 && refused.length === 0 && unexpected.length === 0
      && observed.every((item) => item.run === 1 && item.pass === 1) && packagePasses.every((item) => item.pass === 1);
    save(hook, ".gate/gen/native-contracts/report.json", JSON.stringify({ schema: 1, status: pass ? "pass" : "fail",
      scope: "selected-real-module-consumer-contracts-not-app-qualification", ...bound(hook), command: "go", args,
      execution: action, expected_count: 29, observed, package_passes: packagePasses, refused, unexpected, malformed_lines: malformed,
      ...(error ? { error } : {}) }, null, 2) + "\n");
    if (commandFailure) throw commandFailure;
    hook.assert("Actual twenty-nine top tests and all three packages pass; zero skips/failures", () => pass);
  });
  // Deliberately independent of Go test success and all earlier caller checks.
  hook.check("cat-native-source-format", () => {
    admit(hook);
    const rows = [];
    for (const relative of formatFiles) {
      let before, after, output = "", error;
      try {
        const source = confined(hook.context.root, relative);
        before = fs.readFileSync(source);
        try { output = hook.run("gofmt", [relative], hook.context.root); }
        catch (failure) { output = failure.stdout ?? ""; error = failure.message; }
        after = fs.readFileSync(source);
        const formatted = Buffer.from(output), retained = `.gate/gen/native-format/${relative}`;
        save(hook, retained, formatted);
        rows.push({ file: relative, before_sha256: hash(before), source_after_sha256: hash(after),
          after_sha256: hash(formatted), formatted_file: retained, bytes: formatted.length,
          source_unchanged: before.equals(after), format_unchanged: !error && before.equals(formatted),
          execution: hook.actions.findLast((item) => item.kind === "command" && item.check === "cat-native-source-format"),
          ...(error ? { error } : {}) });
      } catch (failure) { rows.push({ file: relative, error: failure.message, source_unchanged: false, format_unchanged: false }); }
    }
    const pass = rows.length === 20 && rows.every((row) => !row.error && row.source_unchanged && row.format_unchanged && row.execution?.exit_code === 0);
    save(hook, ".gate/gen/native-format/report.json", JSON.stringify({ schema: 1, status: pass ? "pass" : "fail",
      scope: "actual-native-formatter-diagnostic-source-never-rewritten", ...bound(hook), files: rows }, null, 2) + "\n");
    hook.assert("All twenty actual gofmt outputs equal unchanged owning source", () => pass);
  });
}
