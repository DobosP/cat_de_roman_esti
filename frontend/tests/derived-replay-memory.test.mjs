import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";
import ts from "typescript";

const STORAGE_KEY = "cat_derived_replay_v1";
const source = readFileSync(new URL("../src/derivedReplay.ts", import.meta.url), "utf8");
const compiled = ts.transpileModule(source, {
  compilerOptions: { module: ts.ModuleKind.ESNext, target: ts.ScriptTarget.ES2021 },
}).outputText;
const replay = await import(
  `data:text/javascript;base64,${Buffer.from(compiled).toString("base64")}`
);

class MemoryStorage {
  values = new Map();

  getItem(key) {
    return this.values.get(key) ?? null;
  }

  setItem(key, value) {
    this.values.set(key, String(value));
  }

  removeItem(key) {
    this.values.delete(key);
  }

  clear() {
    this.values.clear();
  }
}

const storage = new MemoryStorage();
globalThis.localStorage = storage;

test.beforeEach(() => storage.clear());

test("keeps exactly one opaque completed id per derived game", () => {
  replay.rememberDerivedReplayId("intrusul", "session-intrusul-old");
  replay.rememberDerivedReplayId("intrusul", "session-intrusul-new");
  replay.rememberDerivedReplayId("perechi", "session-perechi");

  assert.equal(replay.lastDerivedReplayId("intrusul"), "session-intrusul-new");
  assert.equal(replay.lastDerivedReplayId("perechi"), "session-perechi");
  assert.deepEqual(JSON.parse(storage.getItem(STORAGE_KEY)), {
    version: 1,
    ids: {
      intrusul: "session-intrusul-new",
      perechi: "session-perechi",
    },
  });
});

test("migrates the bounded direct-map shape and discards unknown fields", () => {
  storage.setItem(
    STORAGE_KEY,
    JSON.stringify({
      intrusul: "legacy-intrusul",
      perechi: "legacy-perechi",
      source_id: "must-not-survive",
      answer: "must-not-survive",
    }),
  );

  assert.equal(replay.lastDerivedReplayId("intrusul"), "legacy-intrusul");
  assert.deepEqual(JSON.parse(storage.getItem(STORAGE_KEY)), {
    version: 1,
    ids: {
      intrusul: "legacy-intrusul",
      perechi: "legacy-perechi",
    },
  });
});

test("rejects oversized and control-character ids without replacing good memory", () => {
  replay.rememberDerivedReplayId("intrusul", "valid-session");
  replay.rememberDerivedReplayId("intrusul", "x".repeat(129));
  replay.rememberDerivedReplayId("perechi", "bad\nvalue");

  assert.equal(replay.lastDerivedReplayId("intrusul"), "valid-session");
  assert.equal(replay.lastDerivedReplayId("perechi"), null);
  assert.deepEqual(Object.keys(JSON.parse(storage.getItem(STORAGE_KEY)).ids), [
    "intrusul",
  ]);
});

test("malformed and future-version documents fail safely without being overwritten", () => {
  storage.setItem(STORAGE_KEY, "{not json");
  assert.equal(replay.lastDerivedReplayId("intrusul"), null);
  assert.equal(storage.getItem(STORAGE_KEY), "{not json");

  const future = JSON.stringify({
    version: 2,
    ids: { intrusul: "future-session" },
  });
  storage.setItem(STORAGE_KEY, future);
  assert.equal(replay.lastDerivedReplayId("intrusul"), null);
  assert.equal(storage.getItem(STORAGE_KEY), future);
});
