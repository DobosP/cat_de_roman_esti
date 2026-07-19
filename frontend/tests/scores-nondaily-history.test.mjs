import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";
import ts from "typescript";

const STORAGE_KEY = "cat_wordgame_scores_v1";
const source = readFileSync(new URL("../src/scores.ts", import.meta.url), "utf8");
const compiled = ts.transpileModule(source, {
  compilerOptions: { module: ts.ModuleKind.ESNext, target: ts.ScriptTarget.ES2021 },
}).outputText;
const scores = await import(`data:text/javascript;base64,${Buffer.from(compiled).toString("base64")}`);

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

test("no history and daily-only history both keep the first normal starter", () => {
  assert.equal(scores.hasCompletedNonDaily("intrusul"), false);

  scores.recordScore("intrusul", 900, "zilnic", { daily: "2026-07-19" });
  assert.equal(scores.hasCompletedNonDaily("intrusul"), false);
});

test("one normal completion permanently consumes starter eligibility", () => {
  scores.recordScore("perechi", 800, "normal");
  assert.equal(scores.hasCompletedNonDaily("perechi"), true);

  // The marker survives the bounded 50-entry recent window even after daily runs age
  // the original normal entry out of it.
  for (let day = 1; day <= 51; day += 1) {
    scores.recordScore("perechi", 700, `zilnic ${day}`, {
      daily: `2026-08-${String(day).padStart(2, "0")}`,
    });
  }
  assert.equal(scores.hasCompletedNonDaily("perechi"), true);
});

test("legacy history infers normal versus daily without a marker", () => {
  const entry = { score: 500, detail: "vechi", at: 1 };
  storage.setItem(
    STORAGE_KEY,
    JSON.stringify({ intrusul: { best: entry, played: 1, recent: [entry] } }),
  );
  assert.equal(scores.hasCompletedNonDaily("intrusul"), true);

  const daily = { ...entry, daily: "2026-07-18" };
  storage.setItem(
    STORAGE_KEY,
    JSON.stringify({ intrusul: { best: daily, played: 1, recent: [daily] } }),
  );
  assert.equal(scores.hasCompletedNonDaily("intrusul"), false);
});

test("malformed local history fails safely to beginner eligibility", () => {
  storage.setItem(STORAGE_KEY, "{not json");
  assert.equal(scores.hasCompletedNonDaily("intrusul"), false);

  storage.setItem(STORAGE_KEY, JSON.stringify({ intrusul: { played: "oops", recent: [{}] } }));
  assert.equal(scores.hasCompletedNonDaily("intrusul"), false);
});
