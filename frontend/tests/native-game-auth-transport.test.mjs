import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";
import vm from "node:vm";
import ts from "@typescript/typescript6";
import * as sharedClient from "@roedu/ui";

function loadModule(path, dependencies, document) {
  const source = readFileSync(new URL(path, import.meta.url), "utf8");
  const code = ts.transpileModule(source, {
    compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022 },
  }).outputText;
  const exported = {};
  vm.runInNewContext(code, { exports: exported, require: (name) => dependencies[name], document, fetch: (...args) => globalThis.fetch(...args) });
  return exported;
}

void test("native gameplay sends real same-origin account credentials and CSRF through the shared transport", async () => {
  const document = { cookie: "csrftoken=synthetic-proof; unrelated=ignored" };
  const auth = loadModule("../src/api/auth.ts", {}, document);
  const client = loadModule("../src/api/client.ts", { "@roedu/ui": sharedClient, "./auth": auth }, document);
  const original = globalThis.fetch;
  const calls = [];
  globalThis.fetch = async (url, init) => {
    calls.push({ url, init });
    return new Response(JSON.stringify({ ok: true }), { status: 200, headers: { "Content-Type": "application/json" } });
  };
  try {
    await client.postJson("/api/wordgames/intrusul/games", { guess: "synthetic-word" });
    assert.equal(calls[0].init.credentials, "same-origin");
    assert.equal(new Headers(calls[0].init.headers).get("X-CSRFToken"), "synthetic-proof");
    assert.equal(new Headers(calls[0].init.headers).get("Content-Type"), "application/json");
    assert.deepEqual(JSON.parse(calls[0].init.body), { guess: "synthetic-word" });
    document.cookie = "";
    await client.postJson("/api/wordgames/intrusul/games");
    assert.equal(new Headers(calls[1].init.headers).get("X-CSRFToken"), null);
    document.cookie = "csrftoken=%malformed";
    await client.postJson("/api/wordgames/intrusul/games");
    assert.equal(new Headers(calls[2].init.headers).get("X-CSRFToken"), null);
  } finally { globalThis.fetch = original; }
});
