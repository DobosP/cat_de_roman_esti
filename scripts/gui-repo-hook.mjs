import * as fs from "node:fs";
import path from "node:path";
import { spawnSync } from "node:child_process";
import { pathToFileURL } from "node:url";
import { createHash } from "node:crypto";

const target = process.argv[2], invocation = process.argv[3];
const root = process.cwd();
const configured = spawnSync("task", ["--silent", "repo:kit-config"], { encoding: "utf8", cwd: root });
if (configured.status !== 0) throw new Error("Actual repo:kit-config failed");
const config = JSON.parse(configured.stdout);
const kitRoot = path.join(root, config.npm_dir);
const { createHook } = await import(pathToFileURL(path.join(kitRoot, "scripts/run-task.mjs")).href);
const hook = createHook(target, invocation);
const frontend = path.join(root, "frontend");
const directory = `.gate/${target.replaceAll(":", "-")}`;
const scratch = path.join(root, directory);
fs.mkdirSync(scratch, { recursive: true });
const hash = (bytes) => createHash("sha256").update(bytes).digest("hex");
function command(check, executable, args, cwd = root, env = {}) {
  hook.check(check, () => hook.run(executable, args, cwd, env));
}
function setup(prefix) {
  command(`${prefix}-npm-ci`, "npm", ["ci", "--no-audit", "--no-fund"], frontend);
}
function frontendBuild(prefix) {
  command(`${prefix}-frontend-build`, "npm", ["run", "build"], frontend);
}
function binaries(prefix) {
  for (const name of ["cat-server", "cat-browser-plan"]) {
    command(`${prefix}-build-${name}`, "go", ["build", "-o", path.join(scratch, name), `./cmd/${name}`], path.join(root, "go-backend"));
    if (fs.existsSync(path.join(scratch, name))) hook.artifact(`${directory}/${name}`);
  }
}
function nativeUnit() {
  for (const [name, module] of [["backend", "go-backend"], ["authcore", "shared-go/authcore"]]) {
    hook.check(`cat-${name}-race`, () => {
      const output = hook.run("go", ["test", "-race", "-json", "./..."], path.join(root, module));
      const skipped = output.split("\n").filter((line) => line.startsWith("{")).map((line) => JSON.parse(line)).filter((event) => event.Action === "skip");
      hook.assert("Only explicit native PG tests may skip without DSN", () => skipped.every((event) =>
        module === "go-backend" && ["github.com/DobosP/cat_de_roman_esti/go-backend/internal/accounts", "github.com/DobosP/cat_de_roman_esti/go-backend/internal/httpapi"].includes(event.Package)));
    });
    command(`cat-${name}-vet`, "go", ["vet", "./..."], path.join(root, module));
  }
  command("cat-doc-check", "go", ["run", "./cmd/cat-doc-check", "--root", ".."], path.join(root, "go-backend"));
  command("cat-content-validate", "go", ["run", "./cmd/cat-content", "validate", "--root", ".."], path.join(root, "go-backend"));
  command("cat-content-export", "go", ["run", "./cmd/cat-content", "export", "--root", "..", "--check"], path.join(root, "go-backend"));
  command("cat-frontend-unit", "npm", ["test"], frontend);
  command("cat-frontend-lint", "npm", ["run", "lint"], frontend);
  command("cat-frontend-types", "npm", ["run", "typecheck"], frontend);
  frontendBuild("cat-unit");
  command("cat-docs-gate", "python3", [path.join(kitRoot, "lint/check_docs.py"), "."]);
}
switch (target) {
  case "setup": setup("cat-setup"); break;
  case "deps":
    hook.check("npm-lock", () => {
      const primary = JSON.parse(fs.readFileSync(".gate/wrapper-current.json")).target;
      const request = JSON.parse(fs.readFileSync("scripts/gui-deps-request.json"));
      hook.assert("Explicit auxiliary-only dependency request", () => request.schema === 1 && request.scope === "baseline-quality-only" && Object.keys(request).length === 2);
      const onlyQuality = primary === "deps";
      const before = ["frontend/package.json", "frontend/package-lock.json", "frontend/vendor/roedu-ui-0.3.0.tgz"].map((file) => hash(fs.readFileSync(file)));
      for (const module of [...(onlyQuality ? [] : ["frontend"]), "tools/gui-baseline-quality"]) hook.run("npm", ["install", "--package-lock-only", "--ignore-scripts"], path.join(root, module));
      if (onlyQuality) hook.assert("Original frontend graph and SDK bytes stayed exact", () => ["frontend/package.json", "frontend/package-lock.json", "frontend/vendor/roedu-ui-0.3.0.tgz"].every((file, index) => hash(fs.readFileSync(file)) === before[index]));
    });
    hook.check("go-mod-tidy", () => {
      for (const module of ["go-backend", "shared-go/authcore"]) hook.run("go", ["mod", "tidy"], path.join(root, module));
    });
    break;
  case "gen": {
    const request = JSON.parse(fs.readFileSync(path.join(root, "scripts/gui-gen-request.json")));
    hook.check("cat-gen-request", () => hook.assert("Explicit committed original qualification request", () =>
      request.schema === 1 && ["qualify-original-react", "capture-original-baseline"].includes(request.operation) && request.fixtures === "frontend/e2e/original/runtime.spec.mjs" && Object.keys(request).length === 3));
    // Plain gen is the E1 original route; it deliberately runs actual prerequisites
    // itself, as canonical setup has no nested gen-context routing in core-v1.1.
    setup("cat-original");
    frontendBuild("cat-original");
    binaries("cat-original");
    hook.check("cat-original-ui-runtime", () => {
      hook.assert("Prerequisite commands passed", () => hook.checks.every((item) => item.status === "pass"));
      const started = new Date().toISOString();
      const output = hook.run("node", ["scripts/gui-original-execution.mjs"], root, {
        CDR_NATIVE_BINARY: path.join(scratch, "cat-server"), CDR_BROWSER_PLAN_BINARY: path.join(scratch, "cat-browser-plan"),
      });
      const finished = new Date().toISOString(), native = JSON.parse(output);
      hook.assert("Actual original native browser outcome", () => native.status === "pass" && native.sha === hook.context.sha && native.tree_sha256 === hook.context.tree_sha256);
      const action = hook.actions.findLast((item) => item.kind === "command");
      const evidence = path.join(scratch, "original/evidence");
      const ref = (name, data) => {
        fs.writeFileSync(path.join(evidence, name), data);
        return { path: `docs/reviews/gui-original-react/${name}`, sha256: hash(data) };
      };
      const report = ref("native-report.json", Buffer.from(output));
      const stdout = ref("stdout.log", fs.readFileSync(path.join(root, action.stdout_log)));
      const stderr = ref("stderr.log", fs.readFileSync(path.join(root, action.stderr_log)));
      const receipt = { ...native, check: "cat-original-ui-runtime", fixtures: native.fixtures.map(({ executed: _executed, ...item }) => ({ ...item, assertions: item.assertions.map(({ executed: _ran, ...assertion }) => assertion) })),
        execution: { kind: "actual-original-runtime", command: "node", args: ["scripts/gui-original-execution.mjs"], exit_code: action.exit_code, started, finished, report, stdout, stderr } };
      fs.writeFileSync(path.join(evidence, "receipt.json"), JSON.stringify(receipt, null, 2) + "\n");
      for (const name of fs.readdirSync(evidence)) hook.artifact(`${directory}/original/evidence/${name}`);
      hook.artifact(`${directory}/original/playwright.json`);
    });
    if (hook.checks.every((item) => item.status === "pass")) command("cat-original-receipt-contract", "node", ["scripts/gui-validate-original-receipt.mjs"]);
    if (hook.checks.every((item) => item.status === "pass")) command("cat-browser-inventory", "node", ["scripts/gui-full-browser.mjs", "inventory"], root, {
      CDR_NATIVE_BINARY: path.join(scratch, "cat-server"), CDR_BROWSER_PLAN_BINARY: path.join(scratch, "cat-browser-plan"),
    });
    if (request.operation === "capture-original-baseline" && hook.checks.every((item) => item.status === "pass")) {
      command("cat-quality-npm-ci", "npm", ["ci", "--no-audit", "--no-fund"], path.join(root, "tools/gui-baseline-quality"));
      command("cat-original-baseline", "node", ["scripts/gui-baseline.mjs", "original-capture"], root, {
        CDR_NATIVE_BINARY: path.join(scratch, "cat-server"), CDR_BROWSER_PLAN_BINARY: path.join(scratch, "cat-browser-plan"),
      });
      if (fs.existsSync(path.join(scratch, "original/baseline/capture.json"))) {
        for (const name of fs.readdirSync(path.join(scratch, "original/baseline"))) hook.artifact(`${directory}/original/baseline/${name}`);
      }
      command("cat-original-budget-boundary", "node", ["scripts/gui-original-budget.mjs"]);
      if (fs.existsSync(path.join(scratch, "original/budget-boundary.json"))) hook.artifact(`${directory}/original/budget-boundary.json`);
    }
    break;
  }
  case "unit": nativeUnit(); break;
  case "build": frontendBuild("cat-build"); command("cat-build-assets", "node", ["scripts/gui-assets.mjs", "sync"]); binaries("cat-build"); break;
  case "assets-sync": command("cat-assets-sync", "node", ["scripts/gui-assets.mjs", "sync"]); break;
  case "legacy-freeze":
    command("cat-legacy-freeze", "node", ["scripts/gui-assets.mjs", "freeze"]);
    if (fs.existsSync(path.join(root, "legacy/original-bundle.json"))) {
      const proof = JSON.parse(fs.readFileSync(path.join(root, "legacy/original-bundle.json")));
      for (const file of [proof.archive, proof.archive + ".sha256", "legacy/original-bundle.json"]) hook.artifact(file);
    }
    break;
  case "baseline":
    frontendBuild("cat-baseline"); binaries("cat-baseline");
    command("cat-baseline-browser", "node", ["scripts/gui-baseline.mjs", "capture"], root, { CDR_NATIVE_BINARY: path.join(scratch, "cat-server"), CDR_BROWSER_PLAN_BINARY: path.join(scratch, "cat-browser-plan") });
    if (fs.existsSync(path.join(root, "baselines/cat/capture.json"))) hook.artifact("baselines/cat/capture.json");
    break;
  case "full":
    nativeUnit(); binaries("cat-full");
    for (const [name, flag] of [["accounts", "accounts.database"], ["httpapi", "arcade.database"]]) {
      hook.check(`cat-pg-${name}`, () => {
        hook.assert("Explicit compose disposable DSN required", () => Boolean(process.env.GATE_DB_DSN));
        const output = hook.run("go", ["test", "-race", "-json", `./internal/${name}`, `-${flag}`, process.env.GATE_DB_DSN], path.join(root, "go-backend"));
        hook.assert("Full PG lane has zero skipped tests", () => !output.split("\n").filter((line) => line.startsWith("{")).map((line) => JSON.parse(line)).some((event) => event.Action === "skip"));
      });
    }
    command("cat-http-parity", "go", ["run", "./cmd/cat-qualify", "parity", "--binary", path.join(scratch, "cat-server")], path.join(root, "go-backend"));
    command("cat-browser-full", "node", ["scripts/gui-full-browser.mjs"], root, { CDR_NATIVE_BINARY: path.join(scratch, "cat-server"), CDR_BROWSER_PLAN_BINARY: path.join(scratch, "cat-browser-plan") });
    hook.browser = { inventory: "frontend/e2e/gui-inventory.json", asset_root: "go-backend/embedfs/dist", entry: "index.html", asset_prefix: "/" };
    break;
  case "e2e": case "perf":
    command(`cat-${target}-browser`, "node", ["scripts/gui-full-browser.mjs", target]); break;
  default: throw new Error(`Unsupported actual repo hook: ${target}`);
}
const report = hook.finish();
process.stdout.write(JSON.stringify(report) + "\n");
process.exitCode = report.checks.some((item) => item.status !== "pass") ? 1 : 0;
