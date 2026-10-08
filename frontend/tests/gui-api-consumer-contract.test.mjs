import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { spawnSync } from "node:child_process";
import { nativeCompiler, parserBinding } from "../scripts/compiler-runtime.mjs";
import { fileURLToPath } from "node:url";
import vm from "node:vm";
import test from "node:test";
import ts from "@typescript/typescript6";
import * as sharedClient from "@roedu/ui";

// These are authored contract checks, not a native API/session fixture. The
// owning trusted runtime must execute them before any old assertion retirement.
const frontend = fileURLToPath(new URL("../", import.meta.url));
const configPath = fileURLToPath(new URL("../tsconfig.json", import.meta.url));

function diagnosticsText(diagnostics) {
  return ts.formatDiagnosticsWithColorAndContext(diagnostics, {
    getCanonicalFileName: (name) => name,
    getCurrentDirectory: () => frontend,
    getNewLine: () => "\n",
  });
}

function installedCompilerOptions() {
  const lock = JSON.parse(readFileSync(new URL("../package-lock.json", import.meta.url), "utf8"));
  parserBinding(frontend, ts);
  const compiler = JSON.parse(readFileSync(new URL("../node_modules/typescript/package.json", import.meta.url), "utf8"));
  assert.equal(compiler.name, "typescript");
  assert.equal(compiler.version, lock.packages["node_modules/typescript"].version,
    "the actual native CLI compiler must match the owning lock");
  const config = ts.readConfigFile(configPath, ts.sys.readFile);
  assert.equal(config.error, undefined, config.error ? diagnosticsText([config.error]) : "");
  const parsed = ts.parseJsonConfigFileContent(config.config, ts.sys, frontend, undefined, configPath);
  assert.equal(parsed.errors.length, 0, diagnosticsText(parsed.errors));
  assert.equal(parsed.options.strict, true, "consumer contracts require the owning strict config");
  return parsed.options;
}

test("real TypeScript consumers retain the exported game API property, union and private-key contracts", () => {
  installedCompilerOptions();
  const cli = nativeCompiler(frontend).executable;
  const version = spawnSync(cli, ["--version"], { cwd: frontend, encoding: "utf8" });
  const compiler = JSON.parse(readFileSync(new URL("../node_modules/typescript/package.json", import.meta.url), "utf8"));
  assert.equal(version.status, 0, version.stderr);
  assert.equal(version.stdout.trim(), `Version ${compiler.version}`);
  // Exact owning strict options are inherited; this project only selects the
  // real consumer fixture. TS6 supplies AST/transpile services, never this check.
  const project = fileURLToPath(new URL("./fixtures/gui-api-consumer-tsconfig.json", import.meta.url));
  const checked = spawnSync(cli, ["--project", project, "--noEmit"], { cwd: frontend, encoding: "utf8" });
  assert.equal(checked.status, 0, `${checked.stdout}${checked.stderr}`);
});

function loadActualModule(path, dependencies, document, options) {
  const filename = fileURLToPath(new URL(path, import.meta.url));
  const source = readFileSync(filename, "utf8");
  const transformed = ts.transpileModule(source, {
    fileName: filename,
    // The real consumer typecheck above keeps the entire owning configuration.
    // This existing transport-harness pattern only adapts the module container
    // for VM loading; bundler resolution is not compatible with CommonJS.
    compilerOptions: {
      module: ts.ModuleKind.CommonJS,
      target: options.target,
      useDefineForClassFields: options.useDefineForClassFields,
    },
    reportDiagnostics: true,
  });
  const errors = (transformed.diagnostics ?? []).filter(({ category }) => category === ts.DiagnosticCategory.Error);
  assert.equal(errors.length, 0, diagnosticsText(errors));
  const exported = {};
  vm.runInNewContext(transformed.outputText, {
    exports: exported,
    require(name) {
      if (!Object.hasOwn(dependencies, name)) throw new Error(`Unbound actual module dependency: ${name}`);
      return dependencies[name];
    },
    document,
    URLSearchParams,
    fetch: (...args) => globalThis.fetch(...args),
  }, { filename });
  return exported;
}

test("actual requestClue encodes opaque reserved-character IDs through the real app client and shared SDK", async () => {
  // Only the fetch boundary is substituted. The ID and reply are explicitly
  // NON-NATIVE transport data: they do not claim server acceptance or privacy qualification.
  const replies = ["rundă/segment?x=1#% Ș", "opaque%2Falready"].map((game_id) => ({
    ok: true, game_id, attempts: 0, won: false, gave_up: false, reachable_count: 100,
    difficulty: "usor", clues_used: 1, clue_available: true, next_clue_kind: "warmer",
    guesses: [], clue_kind: "category", category: { key: "transport-fixture", label: "Transport fixture" },
    message: "NON-NATIVE transport reply",
  }));
  const paths = [
    "/api/wordgames/contexto/games/rund%C4%83%2Fsegment%3Fx%3D1%23%25%20%C8%98/clue",
    "/api/wordgames/contexto/games/opaque%252Falready/clue",
  ];
  const calls = [];
  const originalFetch = globalThis.fetch;
  globalThis.fetch = async (url, init) => {
    calls.push({ url, init });
    assert.ok(calls.length <= replies.length, "unexpected extra transport request");
    return new Response(JSON.stringify(replies[calls.length - 1]), {
      status: 200, headers: { "Content-Type": "application/json" },
    });
  };
  try {
    const options = installedCompilerOptions();
    const document = { cookie: "csrftoken=synthetic-contract-csrf" };
    const auth = loadActualModule("../src/api/auth.ts", {}, document, options);
    const client = loadActualModule("../src/api/client.ts", {
      "@roedu/ui": sharedClient, "./auth": auth,
    }, document, options);
    const contexto = loadActualModule("../src/api/contexto.ts", { "./client": client }, document, options);
    assert.equal(typeof contexto.requestClue, "function");
    for (const [index, reply] of replies.entries()) {
      const result = await contexto.requestClue(reply.game_id);
      assert.deepEqual(result, reply, "the real wrappers must return the actual fetch JSON unchanged");
      assert.equal(calls.length, index + 1);
      const { url, init } = calls[index];
      assert.equal(url, paths[index]);
      const resolved = new URL(url, "https://transport-fixture.invalid");
      assert.equal(resolved.pathname, paths[index]);
      assert.equal(resolved.search, "");
      assert.equal(resolved.hash, "");
      assert.equal(init.method, "POST");
      assert.equal(init.credentials, "same-origin");
      assert.equal(new Headers(init.headers).get("X-CSRFToken"), "synthetic-contract-csrf");
      assert.equal(init.body, undefined, "the clue wrapper has no caller-authored mutation payload");
    }
  } finally {
    globalThis.fetch = originalFetch;
  }
});
