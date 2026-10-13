import * as fs from "node:fs";
import path from "node:path";
import { createHash } from "node:crypto";
import { loadUnitReuse } from "./gui-unit-reuse.mjs";
import { inputKey, classifyGoPackages, createNativeProof, validateNativeReuse } from "./gui-native-reuse.mjs";

const hash = (bytes) => createHash("sha256").update(bytes).digest("hex");
const capsule = ".gate/cat-unit-reuse";
function confined(root, relative) {
  if (!relative || path.isAbsolute(relative) || /[\\:\x00-\x1f\x7f]/.test(relative)
    || relative.split("/").some((part) => !part || part === "." || part === "..")) throw Error("Unsafe reuse artifact path");
  let cursor = root;
  for (const part of relative.split("/")) {
    cursor = path.join(cursor, part);
    try {
      const info = fs.lstatSync(cursor);
      if (info.isSymbolicLink() || (!info.isFile() && !info.isDirectory())) throw Error("Nonregular reuse artifact");
    } catch (error) { if (error.code !== "ENOENT") throw error; }
  }
  return cursor;
}
function read(root, relative) {
  const file = confined(root, relative), before = fs.lstatSync(file);
  const fd = fs.openSync(file, fs.constants.O_RDONLY | fs.constants.O_NOFOLLOW | fs.constants.O_NONBLOCK);
  try {
    const opened = fs.fstatSync(fd);
    if (!opened.isFile() || opened.ino !== before.ino || opened.dev !== before.dev) throw Error("Reuse input replaced");
    const bytes = fs.readFileSync(fd), after = fs.fstatSync(fd), current = fs.lstatSync(file);
    if (before.ino !== current.ino || before.dev !== current.dev || before.size !== after.size
      || before.mtimeMs !== after.mtimeMs || before.ctimeMs !== after.ctimeMs || bytes.length !== after.size) throw Error("Reuse input changed");
    return bytes;
  } finally { fs.closeSync(fd); }
}
function write(root, relative, bytes) {
  const file = confined(root, relative);
  fs.mkdirSync(path.dirname(file), { recursive: true });
  fs.writeFileSync(file, bytes);
}
function save(hook, relative, value) {
  write(hook.context.root, relative, JSON.stringify(value, null, 2) + "\n");
  hook.artifact(relative);
}
function retain(hook, source, prefix) {
  const rows = [];
  for (const [original, bytes] of source.files) {
    const retained = `${prefix}/${original}`;
    write(hook.context.root, retained, bytes);
    hook.artifact(retained);
    rows.push({ original, retained, sha256: hash(bytes) });
  }
  return rows;
}
function promote(hook, source) {
  // Only a completed original unit proof is promoted. The wrapper excludes this
  // directory from source snapshots and keeps one rolling capsule between runs.
  const root = hook.context.root, destination = confined(root, capsule);
  if (fs.existsSync(destination)) {
    // Prove the existing tree contains only our prior copied regular artifacts.
    const prior = JSON.parse(read(root, `${capsule}/manifest.json`));
    if (prior.schema !== 1 || prior.owner !== "cat-gate-native-reuse" || !Array.isArray(prior.files)) throw Error("Unknown reuse capsule owner");
    for (const row of prior.files) if (hash(read(root, `${capsule}/${row.path}`)) !== row.sha256) throw Error("Prior capsule changed");
    const expected = new Set(["manifest.json", ...prior.files.map((row) => row.path)]);
    function verify(directory, prefix = "") {
      for (const entry of fs.readdirSync(directory, { withFileTypes: true })) {
        const name = prefix + entry.name;
        if (entry.isDirectory()) verify(path.join(directory, entry.name), name + "/");
        else if (!entry.isFile() || !expected.delete(name)) throw Error("Unexpected capsule member");
      }
    }
    verify(destination);
    if (expected.size) throw Error("Incomplete capsule");
    fs.rmSync(destination, { recursive: true });
  }
  const files = [];
  for (const [name, bytes] of source.files) {
    write(root, `${capsule}/${name}`, bytes);
    files.push({ path: name, sha256: hash(bytes) });
  }
  write(root, `${capsule}/manifest.json`, JSON.stringify({ schema: 1, owner: "cat-gate-native-reuse", files }) + "\n");
}

export function createGateReuse(hook, config) {
  const ctx = hook.context, prefix = `.gate/${ctx.target}`;
  const context = { ...ctx, config_sha256: hash(JSON.stringify(config)) };
  const unit = ctx.target === "full" ? loadUnitReuse(ctx.root, context) : { status: "miss", reason: "unit executes frontend lanes" };
  let retained = [], promotion = { status: "not-requested" };
  if (unit.status === "hit") {
    retained = retain(hook, unit, `${prefix}/unit-reuse-source`);
    if (unit.files.has(".gate/unit/native-inputs.json")) {
      try { promote(hook, unit); promotion = { status: "retained-original-unit" }; }
      catch (error) {
        // Preserve unrecognized/corrupt cache bytes. Optional promotion must not
        // invalidate the separately verified same-SHA evidence we just retained.
        promotion = { status: "refused", reason: String(error?.message ?? error) };
      }
    }
  }
  save(hook, `${prefix}/unit-reuse.json`, { schema: 1, target: ctx.target, sha: ctx.sha, tree_sha256: ctx.tree_sha256,
    invocation: ctx.invocation, status: unit.status, ...(unit.status === "hit" ? { proof: unit.proof, retained, promotion } : { reason: unit.reason }) });
  return {
    sameSha: unit.status === "hit",
    lane(name) {
      if (unit.status !== "hit") return false;
      hook.check(name, () => hook.assert("Completed same-SHA unit command, assertions and retained streams verify", () =>
        unit.proof.lanes.some((lane) => lane.name === name) && retained.every((row) => hash(read(ctx.root, row.retained)) === row.sha256)));
      return true;
    },
    native() {
      let selection = { status: "miss", reason: "native input discovery unavailable" }, current;
      hook.check("cat-native-reuse-inputs", () => {
        try {
          hook.run("node", ["scripts/gui-native-reuse.mjs", "graph", ctx.target]);
          const graph = classifyGoPackages(read(ctx.root, `${prefix}/native-reuse/graph.stdout.json`));
          current = createNativeProof({ input: inputKey(ctx.root), graph, context: ctx });
          save(hook, `${prefix}/native-inputs.json`, current);
          let original;
          try {
            const source = JSON.parse(read(ctx.root, `${capsule}/.gate/unit/result.json`));
            original = loadUnitReuse(ctx.root, { ...context, target: "full", sha: source.sha, tree_sha256: source.tree_sha256 },
              confined(ctx.root, capsule));
            if (original.status !== "hit") throw Error(original.reason);
            const proof = JSON.parse(original.files.get(".gate/unit/native-inputs.json"));
            if (proof.sha !== source.sha || proof.tree_sha256 !== source.tree_sha256) throw Error("Native proof differs from source unit");
            const backend = original.proof.lanes.find((lane) => lane.name === "cat-backend-race");
            selection = validateNativeReuse({ proof, current,
              graphOutput: original.files.get(".gate/unit/native-reuse/graph.stdout.json"),
              raceOutput: original.files.get(backend.stdout_log) });
            selection.source_result_sha256 = original.proof.result_sha256;
            selection.retained = retain(hook, original, `${prefix}/native-reuse-source`);
          } catch (error) { selection = { status: "miss", reason: String(error?.message ?? error) }; }
          hook.assert("Actual native input key and race-enabled package graph recorded", () => !!current);
        } finally {
          for (const name of ["graph.stdout.json", "graph.stderr.log", "graph-command.json", "graph.json"]) {
            const file = `${prefix}/native-reuse/${name}`;
            if (fs.existsSync(confined(ctx.root, file))) hook.artifact(file);
          }
        }
      });
      save(hook, `${prefix}/native-reuse/selection.json`, { schema: 1, sha: ctx.sha, tree_sha256: ctx.tree_sha256,
        invocation: ctx.invocation, ...selection });
      return {
        selection,
        assertUnchanged() {
          hook.assert("Reused packages retain exact native inputs and verified original race streams", () =>
            selection.status === "hit" && inputKey(ctx.root).digest === current.input_sha256
              && selection.retained.every((row) => hash(read(ctx.root, row.retained)) === row.sha256));
        },
      };
    },
  };
}
