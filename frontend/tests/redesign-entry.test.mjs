import assert from "node:assert/strict";
import { beforeEach, test } from "node:test";
import { readFileSync } from "node:fs";
import ts from "@typescript/typescript6";

function compile(path, imports = {}) {
  const source = readFileSync(new URL(path, import.meta.url), "utf8");
  const js = ts.transpileModule(source, { compilerOptions: {
    module: ts.ModuleKind.ESNext, target: ts.ScriptTarget.ES2021,
  } }).outputText;
  const bound = Object.entries(imports).reduce((code, [name, url]) => code.replace(`"${name}"`, `"${url}"`), js);
  return `data:text/javascript;base64,${Buffer.from(bound).toString("base64")}`;
}

const {
  dailyStatus, localDay, markDailyDone, markDailyStarted, readFreeOptions, roundEntry, writeFreeOptions,
} = await import(compile("../src/entry.ts", { "./categories": compile("../src/categories.ts") }));
const day = "2026-11-16";
const yesterday = "2026-11-15";
const game = "conexiuni";

beforeEach(() => {
  const values = new Map();
  Object.defineProperty(globalThis, "localStorage", {
    configurable: true,
    value: { getItem: (key) => values.get(key) ?? null, setItem: (key, value) => values.set(key, value) },
  });
});

void test("daily comes before a saved free round and completes once on that date for that game", () => {
  const saved = { game_id: "free", terminal: false };
  assert.deepEqual(roundEntry(game, day, saved), { kind: "daily", daily: day });
  markDailyStarted(game, day);
  assert.deepEqual(dailyStatus(game, day), { started: true, done: false });
  assert.deepEqual(roundEntry(game, day, saved), { kind: "daily", daily: day });
  markDailyDone(game, day);
  markDailyStarted(game, day);
  assert.deepEqual(dailyStatus(game, day), { started: true, done: true });
  assert.deepEqual(roundEntry(game, day, saved), { kind: "resume", gameId: "free" });
  assert.deepEqual(roundEntry(game, day, { ...saved, terminal: true }), { kind: "free" });
  assert.deepEqual(roundEntry("intrusul", day), { kind: "daily", daily: day });
  assert.deepEqual(roundEntry(game, "2026-11-17"), { kind: "daily", daily: "2026-11-17" });
});

void test("an unfinished daily keeps its original date including across midnight", () => {
  for (const daily of [yesterday, day]) {
    assert.deepEqual(roundEntry(game, day, { game_id: "daily", daily, terminal: false }),
      { kind: "resume", gameId: "daily", daily });
  }
  assert.deepEqual(roundEntry(game, day, { game_id: "daily", daily: yesterday, terminal: true }),
    { kind: "daily", daily: day });
  assert.equal(localDay(new Date(2026, 10, 15, 23, 59)), yesterday);
  assert.equal(localDay(new Date(2026, 10, 16, 0, 0)), day);
});

void test("free options are validated and stored per game", () => {
  writeFreeOptions(game, { difficulty: "greu", category: "istorie" });
  assert.deepEqual(readFreeOptions(game), { difficulty: "greu", category: "istorie" });
  assert.deepEqual(readFreeOptions("lant"), { difficulty: "usor", category: null });
  writeFreeOptions(game, { difficulty: "hard", category: "unregistered" });
  assert.deepEqual(readFreeOptions(game), { difficulty: "usor", category: null });
});

void test("denied storage behaves as a first visit", () => {
  Object.defineProperty(globalThis, "localStorage", {
    configurable: true,
    get() { throw new Error("Storage denied"); },
  });
  markDailyDone(game, day);
  assert.deepEqual(dailyStatus(game, day), { started: false, done: false });
  assert.deepEqual(roundEntry(game, day), { kind: "daily", daily: day });
  assert.deepEqual(readFreeOptions(game), { difficulty: "usor", category: null });
});
