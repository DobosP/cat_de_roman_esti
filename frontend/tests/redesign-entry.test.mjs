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

let dailyStatus, localDay, markDailyDone, markDailyStarted, readFreeOptions, roundEntry, writeFreeOptions;
let readLocalValue, writeLocalValue, useActiveGame;
let page = 0;
async function freshPage() {
  const storage = compile("../src/pageStorage.ts") + `#${++page}`;
  ({ readLocalValue, writeLocalValue } = await import(storage));
  ({ dailyStatus, localDay, markDailyDone, markDailyStarted, readFreeOptions, roundEntry, writeFreeOptions } =
    await import(compile("../src/entry.ts", {
      "./categories": compile("../src/categories.ts"),
      "./pageStorage": storage,
    })));
  const hooks = `data:text/javascript;base64,${Buffer.from("export const useMemo = (factory) => factory();").toString("base64")}`;
  ({ useActiveGame } = await import(compile("../src/hooks/useActiveGame.ts", {
    "preact/hooks": hooks, "../pageStorage": storage,
  })));
}
const day = "2026-11-16";
const yesterday = "2026-11-15";
const game = "conexiuni";

beforeEach(async () => {
  const values = new Map();
  Object.defineProperty(globalThis, "localStorage", {
    configurable: true,
    value: {
      getItem: (key) => values.get(key) ?? null,
      setItem: (key, value) => values.set(key, value),
      removeItem: (key) => values.delete(key),
    },
  });
  await freshPage();
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

for (const failure of ["getter", "methods", "quota"]) {
  void test(`${failure} storage keeps daily, options and the saved round until reload`, async () => {
    const key = "cat_daily_v2_conexiuni";
    localStorage.setItem(key, "{}");
    const persistent = localStorage;
    if (failure === "getter") Object.defineProperty(globalThis, "localStorage", {
      configurable: true, get() { throw new Error("Storage denied"); },
    });
    else Object.defineProperty(globalThis, "localStorage", {
      configurable: true,
      value: {
        getItem: failure === "methods" ? () => { throw new Error("Read denied"); } : (key) => persistent.getItem(key),
        setItem: () => { throw new Error("Quota exceeded"); },
        removeItem: () => { throw new Error("Write denied"); },
      },
    });

    assert.deepEqual(roundEntry(game, day), { kind: "daily", daily: day });
    markDailyStarted(game, day);
    markDailyDone(game, day);
    markDailyStarted(game, day);
    assert.deepEqual(dailyStatus(game, day), { started: true, done: true });
    assert.deepEqual(roundEntry(game, day), { kind: "free" });
    assert.equal(persistent.getItem(key), "{}");
    writeFreeOptions(game, { difficulty: "greu", category: "istorie" });
    assert.deepEqual(readFreeOptions(game), { difficulty: "greu", category: "istorie" });

    const active = useActiveGame(game);
    active.remember("daily-round");
    assert.equal(useActiveGame(game).peek(), "daily-round");
    assert.equal(active.isCurrent("daily-round"), true);
    assert.equal(active.forgetIfCurrent("another-round"), false);
    assert.equal(active.forgetIfCurrent("daily-round"), true);
    assert.equal(active.peek(), null);

    await freshPage();
    assert.deepEqual(roundEntry(game, day), { kind: "daily", daily: day });
    assert.deepEqual(readFreeOptions(game), { difficulty: "usor", category: null });
    assert.equal(useActiveGame(game).peek(), null);
  });
}

void test("an unsuccessful removal hides the old stored id for this page", () => {
  const key = "cat_active_game_v1_conexiuni";
  localStorage.setItem(key, "saved-id");
  localStorage.removeItem = () => { throw new Error("Removal denied"); };
  const active = useActiveGame(game);
  assert.equal(active.forgetIfCurrent("saved-id"), true);
  assert.equal(localStorage.getItem(key), "saved-id");
  assert.equal(active.peek(), null);
});

void test("read failures use the last observed value and successful storage still sees other tabs", () => {
  const key = "cat_active_game_v1_conexiuni";
  localStorage.setItem(key, "old");
  assert.equal(readLocalValue(key), "old");
  localStorage.setItem(key, "another-tab");
  assert.equal(readLocalValue(key), "another-tab");
  localStorage.getItem = () => { throw new Error("Read denied"); };
  assert.equal(readLocalValue(key), "another-tab");
  writeLocalValue(key, "new");
  assert.equal(readLocalValue(key), "new");
});
