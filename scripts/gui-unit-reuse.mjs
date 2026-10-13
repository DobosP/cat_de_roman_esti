// Optional same-source evidence reuse. A miss always means execute the real lanes.
// No filesystem reads, writes or gate claims occur at import time.
import * as fs from "node:fs";
import path from "node:path";
import { createHash } from "node:crypto";

const hash = (bytes) => createHash("sha256").update(bytes).digest("hex");
const HEX = /^[a-f0-9]{64}$/;
const SHA = /^[a-f0-9]{40}(?:[a-f0-9]{24})?$/;
const UUID = /^[a-f0-9]{8}-[a-f0-9]{4}-4[a-f0-9]{3}-[89ab][a-f0-9]{3}-[a-f0-9]{12}$/;
const PREFIX = ".gate/unit/";
const identityLabel = "Backend race requires fresh synced assets and compiled identity inputs";
const skipLabel = "Only explicit native PG tests may skip without DSN";
export const UNIT_REUSE_LANES = Object.freeze([
  "cat-frontend-unit", "cat-frontend-lint", "cat-frontend-types",
  "cat-backend-race", "cat-backend-vet", "cat-authcore-race", "cat-authcore-vet",
]);
const laneCommands = [
  ["npm", ["test"], "frontend", []],
  ["npm", ["run", "lint"], "frontend", []],
  ["npm", ["run", "typecheck"], "frontend", []],
  ["go", ["test", "-race", "-timeout=30m", "-count=1", "-json", "./..."], "go-backend", [identityLabel, skipLabel]],
  ["go", ["vet", "./..."], "go-backend", [identityLabel.replace("race", "vet")]],
  ["go", ["test", "-race", "-json", "./..."], "shared-go/authcore", [skipLabel]],
  ["go", ["vet", "./..."], "shared-go/authcore", []],
];
const requiredChecks = ["bootstrap-evidence", "cat-setup-npm-ci", "versions-check", "toolchain-versions", "lint-scope", "kit:check",
  "cat-active-ui", "cat-doccheck-source-contracts", "cat-doc-check", "cat-content-validate", "cat-content-export", "cat-docs-gate",
  "cat-unit-fresh-build-output", "cat-unit-frontend-build", "cat-unit-emitted-inventory", "cat-unit-assets", "cat-unit-gui-identity",
  "cat-route-budgets", "cat-frozen-legacy-integrity", ...UNIT_REUSE_LANES];
const own = (value, required, optional = []) => value !== null && typeof value === "object" && !Array.isArray(value)
  && required.every((key) => Object.hasOwn(value, key)) && Object.keys(value).every((key) => required.includes(key) || optional.includes(key));
const integer = (value) => Number.isInteger(value) && value >= 0;
const time = (value) => typeof value === "string" && /^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d(?:\.\d{3})?Z$/.test(value) && Number.isFinite(Date.parse(value));
function demand(condition, message) { if (!condition) throw Error(message); }
function relative(value) {
  demand(typeof value === "string" && value.length > 0 && !value.startsWith("/") && !/[\\\x00-\x1f\x7f]/.test(value)
    && value.split("/").every((part) => part && part !== "." && part !== ".."), "unsafe evidence path");
  return value;
}
function artifactIndex(values) {
  demand(Array.isArray(values), "missing artifact list");
  const index = new Map();
  for (const value of values) {
    const match = typeof value === "string" && /^(.+) sha256:([a-f0-9]{64})$/.exec(value);
    demand(match && !index.has(relative(match[1])), "malformed or duplicate artifact");
    index.set(match[1], match[2]);
  }
  return index;
}
function commandShape(action, bootstrap = false) {
  return own(action, [bootstrap ? "phase" : "check", "kind", "command", "argument_count", "args_sha256", "cwd", "exit_code", "duration_ms",
    "stdout_sha256", "stderr_sha256", "stdout_log", "stderr_log"])
    && action.kind === "command" && typeof action.command === "string" && action.command.length > 0
    && integer(action.argument_count) && HEX.test(action.args_sha256) && action.exit_code === 0 && integer(action.duration_ms)
    && HEX.test(action.stdout_sha256) && HEX.test(action.stderr_sha256);
}

// Exported pure validator permits hostile-evidence tests without writing fake gate
// receipts. read returns exact bytes; the production loader below confines it.
export function validateUnitReuse(context, read) {
  demand(context.target === "full" && context.dirty === false && SHA.test(context.sha) && HEX.test(context.tree_sha256)
    && /^sha256:[a-f0-9]{64}$/.test(context.toolchain_digest) && ["enforced", "report-only"].includes(context.stage)
    && integer(context.parallel) && context.parallel >= 1 && context.parallel <= 4 && HEX.test(context.config_sha256)
    && time(context.started), "current full identity is incomplete or dirty");
  const files = new Map();
  const retain = (name, expected) => {
    demand(name.startsWith(PREFIX), "evidence outside unit target"); relative(name);
    const bytes = files.get(name) ?? Buffer.from(read(name));
    if (expected !== undefined) demand(HEX.test(expected) && hash(bytes) === expected, `artifact hash differs: ${name}`);
    files.set(name, bytes); return bytes;
  };
  const resultBytes = retain(`${PREFIX}result.json`), result = JSON.parse(resultBytes);
  demand(own(result, ["schema", "target", "status", "sha", "dirty", "tree_sha256", "toolchain_digest", "versions_lock_sha256", "parallel",
    "started", "finished", "checks", "csp", "budgets", "artifacts"], ["legacy_pending"])
    && result.schema === 1 && result.target === "unit" && result.status === "pass" && result.dirty === false
    && ["sha", "tree_sha256", "toolchain_digest"].every((key) => result[key] === context[key])
    && result.versions_lock_sha256 === hash(read("versions.lock.json")) && result.parallel === context.parallel
    && time(result.started) && time(result.finished) && Date.parse(result.finished) >= Date.parse(result.started)
    && Date.parse(result.finished) <= Date.parse(context.started), "unit result identity/status differs");
  demand(own(result.csp, ["stage", "violations", "legacy_violations"]) && result.csp.stage === context.stage
    && result.csp.violations === 0 && result.csp.legacy_violations === 0, "unit CSP identity/status differs");
  demand(result.budgets && typeof result.budgets === "object" && !Array.isArray(result.budgets)
    && Object.values(result.budgets).every((item) => item && ["pass", "recorded"].includes(item.status)
      && integer(item.actual) && (item.limit === null || integer(item.limit))), "unit budgets contain a failure");
  demand(!result.legacy_pending?.length, "unit has pending legacy findings");
  demand(Array.isArray(result.checks), "missing unit checks");
  const checks = new Map();
  for (const check of result.checks) {
    demand(own(check, ["name", "status", "duration_ms"], ["reason"]) && typeof check.name === "string" && !checks.has(check.name)
      && check.status === "pass" && integer(check.duration_ms), "duplicate, failed or invalid unit check");
    checks.set(check.name, check);
  }
  demand(requiredChecks.every((name) => checks.has(name)), "required unit check missing");
  const artifacts = artifactIndex(result.artifacts);
  const evidenced = (name) => { demand(artifacts.has(name), `result lacks artifact: ${name}`); return retain(name, artifacts.get(name)); };
  const executionBytes = evidenced(`${PREFIX}execution.json`), execution = JSON.parse(executionBytes);
  demand(own(execution, ["schema", "invocation", "sha", "tree_sha256", "actions"]) && execution.schema === 1 && UUID.test(execution.invocation)
    && execution.sha === result.sha && execution.tree_sha256 === result.tree_sha256 && Array.isArray(execution.actions), "unit execution identity differs");

  // The target-local wrapper survives the next wrapper invocation. Its UUID is
  // intentionally distinct from the inner SDK invocation linked by bootstrap.
  const wrapperBytes = retain(`${PREFIX}wrapper-current.json`), wrapper = JSON.parse(wrapperBytes);
  demand(own(wrapper, ["schema", "invocation", "target", "sha", "tree_sha256", "toolchain_digest", "config_sha256", "config_path", "config_file_sha256"], ["operator"])
    && (wrapper.operator === undefined || wrapper.operator === null || /^(paul|agent:[a-z0-9][a-z0-9-]{1,39})$/.test(wrapper.operator))
    && wrapper.schema === 1 && wrapper.target === "unit" && UUID.test(wrapper.invocation) && wrapper.invocation !== execution.invocation
    && ["sha", "tree_sha256", "toolchain_digest"].every((key) => wrapper[key] === result[key])
    && wrapper.config_path === `${PREFIX}wrapper-kit-config.json` && wrapper.config_sha256 === context.config_sha256 && HEX.test(wrapper.config_file_sha256), "unit wrapper identity differs");
  const configBytes = retain(wrapper.config_path, wrapper.config_file_sha256), captured = JSON.parse(configBytes);
  demand(own(captured, ["schema", "target", "sha", "tree_sha256", "toolchain_digest", "config", "config_sha256", "command"])
    && ["schema", "target", "sha", "tree_sha256", "toolchain_digest", "config_sha256"].every((key) => captured[key] === wrapper[key])
    && captured.config?.role === "consumer" && captured.config.app === "cat_de_roman_esti"
    && hash(JSON.stringify(captured.config)) === wrapper.config_sha256
    && own(captured.command, ["command", "args", "exit_code", "duration_ms", "stdout_sha256", "stderr_sha256"])
    && captured.command.command === "task" && JSON.stringify(captured.command.args) === '["--silent","repo:kit-config"]'
    && captured.command.exit_code === 0 && integer(captured.command.duration_ms)
    && HEX.test(captured.command.stdout_sha256) && captured.command.stderr_sha256 === hash(""), "unit wrapper config differs");
  const bootstrap = JSON.parse(evidenced(`${PREFIX}bootstrap-execution.json`));
  demand(own(bootstrap, ["schema", "target", "invocation", "sha", "tree_sha256", "toolchain_digest", "started", "config", "config_sha256",
    "wrapper_target", "wrapper_config", "wrapper_config_sha256", "wrapper_invocation", "wrapper_descriptor", "wrapper_descriptor_sha256", "actions", "artifacts", "finished"])
    && bootstrap.schema === 1 && bootstrap.target === "unit" && bootstrap.invocation === execution.invocation
    && ["sha", "tree_sha256", "toolchain_digest"].every((key) => bootstrap[key] === result[key])
    && JSON.stringify(bootstrap.config) === JSON.stringify(captured.config) && bootstrap.config_sha256 === wrapper.config_sha256
    && bootstrap.wrapper_target === "unit" && bootstrap.wrapper_invocation === wrapper.invocation
    && bootstrap.wrapper_config === wrapper.config_path && bootstrap.wrapper_config_sha256 === hash(configBytes)
    && bootstrap.wrapper_descriptor === ".gate/wrapper-current.json" && bootstrap.wrapper_descriptor_sha256 === hash(wrapperBytes)
    && time(bootstrap.started) && time(bootstrap.finished) && Date.parse(bootstrap.finished) >= Date.parse(bootstrap.started)
    && bootstrap.started === result.started && Date.parse(bootstrap.finished) <= Date.parse(result.finished)
    && Array.isArray(bootstrap.actions) && bootstrap.actions.length > 0,
  "unit bootstrap does not bind wrapper and inner invocations");
  const bootstrapArtifacts = artifactIndex(bootstrap.artifacts), bootstrapLogs = new Set();
  for (const action of bootstrap.actions) {
    demand(commandShape(action, true) && /^[A-Za-z][A-Za-z0-9._-]*$/.test(action.phase) && action.cwd === ".", "invalid bootstrap command");
    for (const stream of ["stdout", "stderr"]) {
      const name = action[`${stream}_log`];
      demand(typeof name === "string" && name.startsWith(`${PREFIX}logs/${execution.invocation}-bootstrap-`)
        && !bootstrapLogs.has(name) && bootstrapArtifacts.get(name) === action[`${stream}_sha256`]
        && artifacts.get(name) === action[`${stream}_sha256`], "bootstrap stream binding differs");
      bootstrapLogs.add(name); evidenced(name);
    }
  }
  demand(bootstrapLogs.size === bootstrapArtifacts.size, "unbound bootstrap artifact");
  const laneLogs = new Set(), lanes = [];
  for (const [index, name] of UNIT_REUSE_LANES.entries()) {
    const [command, args, cwd, labels] = laneCommands[index], actions = execution.actions.filter((action) => action.check === name);
    const commands = actions.filter((action) => action.kind === "command"), assertions = actions.filter((action) => action.kind === "assertion");
    const action = commands[0];
    demand(commands.length === 1 && actions.length === 1 + labels.length && assertions.length === labels.length
      && labels.every((label) => assertions.filter((item) => item.label === label).length === 1)
      && assertions.every((item) => own(item, ["check", "kind", "label", "passed", "duration_ms"]) && item.passed === true && integer(item.duration_ms))
      && commandShape(action) && action.command === command && action.cwd === cwd && action.argument_count === args.length
      && action.args_sha256 === hash(JSON.stringify(args)), `lane command/assertion differs: ${name}`);
    for (const stream of ["stdout", "stderr"]) {
      const file = action[`${stream}_log`];
      demand(typeof file === "string" && new RegExp(`^\\.gate/unit/logs/${execution.invocation}-${name}-[0-9]+\\.${stream}\\.log$`).test(file)
        && !laneLogs.has(file) && artifacts.get(file) === action[`${stream}_sha256`], `lane stream binding differs: ${name}`);
      laneLogs.add(file); evidenced(file);
    }
    lanes.push({ name, command, args, cwd, action_sha256: hash(JSON.stringify(action)), stdout_log: action.stdout_log,
      stdout_sha256: action.stdout_sha256, stderr_log: action.stderr_log, stderr_sha256: action.stderr_sha256 });
  }
  // Native input closure is optional for same-SHA reuse; its separate validator
  // decides whether it admits cross-SHA race reuse. Preserve only bound bytes.
  if (artifacts.has(`${PREFIX}native-inputs.json`)) {
    evidenced(`${PREFIX}native-inputs.json`);
    for (const name of ["graph.stdout.json", "graph.stderr.log", "graph-command.json", "graph.json"]) {
      const file = `${PREFIX}native-reuse/${name}`;
      if (artifacts.has(file)) evidenced(file);
    }
  }
  return { status: "hit", files, proof: { schema: 1, policy: "same-sha-passing-unit", source: `${PREFIX}result.json`,
    result_sha256: hash(resultBytes), execution_sha256: hash(executionBytes), invocation: execution.invocation,
    wrapper_invocation: wrapper.invocation, sha: result.sha, tree_sha256: result.tree_sha256, toolchain_digest: result.toolchain_digest,
    versions_lock_sha256: result.versions_lock_sha256, config_sha256: wrapper.config_sha256, parallel: result.parallel,
    stage: result.csp.stage, started: result.started, finished: result.finished, lanes } };
}

// evidenceRoot may be an owning retained capsule with the original `.gate/unit`
// layout. Live versions.lock.json is always read from root, never the capsule.
export function loadUnitReuse(root, context, evidenceRoot = root) {
  try {
    for (const base of new Set([root, evidenceRoot])) {
      demand(typeof base === "string" && path.isAbsolute(base) && path.resolve(base) === base, "canonical root required");
      for (let cursor = base; ; cursor = path.dirname(cursor)) {
        const stat = fs.lstatSync(cursor);
        demand(stat.isDirectory() && !stat.isSymbolicLink(), "symlinked or nonregular root");
        if (path.dirname(cursor) === cursor) break;
      }
    }
    // Any failure marker invalidates the preceding successful SDK result,
    // including malformed, empty, directory or dangling-symlink markers.
    let wrapperFailed = false;
    try { fs.lstatSync(path.join(evidenceRoot, PREFIX, "wrapper-fail.json")); wrapperFailed = true; }
    catch (error) { if (error.code !== "ENOENT") throw error; }
    demand(!wrapperFailed, "unit wrapper failure marker present");
    const read = (name) => {
      relative(name);
      demand(name === "versions.lock.json" || name.startsWith(PREFIX), "read outside unit evidence scope");
      let cursor = name === "versions.lock.json" ? root : evidenceRoot;
      const parts = name.split("/");
      for (const [index, part] of parts.entries()) {
        cursor = path.join(cursor, part);
        const stat = fs.lstatSync(cursor);
        demand(!stat.isSymbolicLink() && (index === parts.length - 1 ? stat.isFile() : stat.isDirectory()), "nonregular evidence path");
      }
      const before = fs.lstatSync(cursor, { bigint: true });
      const fd = fs.openSync(cursor, fs.constants.O_RDONLY | fs.constants.O_NOFOLLOW | fs.constants.O_NONBLOCK);
      try {
        const opened = fs.fstatSync(fd, { bigint: true });
        demand(opened.isFile() && opened.ino === before.ino && opened.dev === before.dev
          && fs.realpathSync(cursor) === cursor && fs.realpathSync(`/proc/self/fd/${fd}`) === cursor, "evidence alias or replacement while opening");
        const bytes = fs.readFileSync(fd), after = fs.fstatSync(fd, { bigint: true }), current = fs.lstatSync(cursor, { bigint: true });
        demand(current.isFile() && !current.isSymbolicLink() && current.ino === after.ino && current.dev === after.dev
          && before.size === after.size && before.mtimeNs === after.mtimeNs && after.size === BigInt(bytes.length), "evidence changed while reading");
        return bytes;
      } finally { fs.closeSync(fd); }
    };
    return validateUnitReuse(context, read);
  } catch (error) { return { status: "miss", reason: String(error?.message ?? error) }; }
}
