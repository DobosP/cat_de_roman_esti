import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";
import ts from "@typescript/typescript6";

const STORAGE_KEY = "cat_wordgame_scores_v1";
const scoreSource = readFileSync(new URL("../src/scores.ts", import.meta.url), "utf8");
const compiled = ts.transpileModule(scoreSource, {
  compilerOptions: { module: ts.ModuleKind.ESNext, target: ts.ScriptTarget.ES2021 },
}).outputText;
const scores = await import(
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

  clear() {
    this.values.clear();
  }
}

const storage = new MemoryStorage();
globalThis.localStorage = storage;

test.beforeEach(() => storage.clear());

// ------------------------------------------------------------------ (a) local daily streak

void test("same-day recording is idempotent", () => {
  scores.recordScore("alchimie", 100, "azi 1", { daily: "2026-07-20" });
  scores.recordScore("intrusul", 0, "azi 2", { daily: "2026-07-20" });
  assert.equal(scores.getDailyStreak("2026-07-20"), 1);
});

void test("a consecutive calendar day increments the streak", () => {
  scores.recordScore("alchimie", 100, "ziua 1", { daily: "2026-07-20" });
  scores.recordScore("perechi", 0, "ziua 2", { daily: "2026-07-21" });
  assert.equal(scores.getDailyStreak("2026-07-21"), 2);
  // Still valid the same day it landed, and while it can still be extended tomorrow.
  assert.equal(scores.getDailyStreak("2026-07-22"), 2);
});

void test("a gap resets the streak to 1", () => {
  scores.recordScore("alchimie", 100, "ziua 1", { daily: "2026-07-20" });
  scores.recordScore("perechi", 0, "ziua 2", { daily: "2026-07-21" });
  scores.recordScore("conexiuni", 0, "revenire", { daily: "2026-07-25" });
  assert.equal(scores.getDailyStreak("2026-07-25"), 1);
  // Two full days without a completion since the last one reads as broken.
  assert.equal(scores.getDailyStreak("2026-07-27"), 0);
});

void test("zero-score daily completions still count toward the streak", () => {
  scores.recordScore("lant", 0, "pierdut", { daily: "2026-07-20" });
  assert.equal(scores.getDailyStreak("2026-07-20"), 1);
});

void test("malformed or absent streak payloads never throw and recompute conservatively", () => {
  assert.equal(scores.getDailyStreak("2026-07-20"), 0);

  storage.setItem(STORAGE_KEY, "{not json");
  assert.doesNotThrow(() => scores.getDailyStreak("2026-07-20"));
  assert.equal(scores.getDailyStreak("2026-07-20"), 0);

  storage.setItem(
    STORAGE_KEY,
    JSON.stringify({
      alchimie: {
        recent: [
          { score: 10, detail: "a", at: 1, daily: "2026-07-18" },
          { score: 0, detail: "b", at: 2, daily: "2026-07-19" },
        ],
      },
      perechi: {
        recent: [{ score: 5, detail: "c", at: 3, daily: "2026-07-20" }],
      },
      _streak: "garbled",
    }),
  );
  assert.equal(scores.getDailyStreak("2026-07-20"), 3);

  storage.setItem(
    STORAGE_KEY,
    JSON.stringify({
      alchimie: { recent: [] },
      _streak: { lastDate: "not-a-date", length: 900 },
    }),
  );
  assert.doesNotThrow(() => scores.getDailyStreak("2026-07-20"));
  assert.equal(scores.getDailyStreak("2026-07-20"), 0);
});

void test("importing history never overwrites the existing local streak", () => {
  scores.recordScore("alchimie", 100, "ziua 1", { daily: "2026-07-20" });
  scores.recordScore("perechi", 0, "ziua 2", { daily: "2026-07-21" });
  assert.equal(scores.getDailyStreak("2026-07-21"), 2);

  scores.importScores(
    JSON.stringify({
      games: { conexiuni: { played: 1, recent: [{ score: 10, detail: "x", at: 9 }] } },
    }),
  );
  assert.equal(scores.getDailyStreak("2026-07-21"), 2);
});

void test("imported daily rows cannot create a streak on a fresh device", () => {
  scores.importScores(
    JSON.stringify({
      games: {
        alchimie: {
          recent: [
            { score: 10, detail: "import 1", at: 1, daily: "2026-07-20" },
            { score: 20, detail: "import 2", at: 2, daily: "2026-07-21" },
          ],
        },
      },
    }),
  );
  assert.equal(scores.getDailyStreak("2026-07-21"), 0);
  assert.deepEqual(JSON.parse(storage.getItem(STORAGE_KEY))._streak, {
    lastDate: "",
    length: 0,
  });
});

void test("export leaves the device-local streak out of portable history", () => {
  scores.recordScore("alchimie", 10, "local", { daily: "2026-07-20" });
  const exported = JSON.parse(scores.exportScores());
  assert.equal(exported.games._streak, undefined);
});

void test("clearing scores also clears the local streak", () => {
  scores.recordScore("alchimie", 100, "ziua 1", { daily: "2026-07-20" });
  scores.clearScores();
  assert.equal(scores.getDailyStreak("2026-07-20"), 0);
});
