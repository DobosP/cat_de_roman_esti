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

function lose(game, attempt) {
  scores.recordScore(game, 0, `pierdut ${attempt}`);
}

test("one or two normal losses keep the derived starter shelf", () => {
  assert.equal(scores.needsDerivedStarter("intrusul"), true);
  lose("intrusul", 1);
  assert.equal(scores.needsDerivedStarter("intrusul"), true);
  lose("intrusul", 2);
  assert.equal(scores.needsDerivedStarter("intrusul"), true);

  const record = scores.scoreBoard().intrusul;
  assert.equal(record.nonDailyCompletions, 2);
  assert.equal(record.nonDailyWon, false);
});

test("one positive normal result graduates immediately", () => {
  scores.recordScore("perechi", 100, "câștigat");
  lose("perechi", 2);
  assert.equal(scores.needsDerivedStarter("perechi"), false);

  const record = scores.scoreBoard().perechi;
  assert.equal(record.nonDailyCompletions, 2);
  assert.equal(record.nonDailyWon, true);
});

test("three normal losses graduate without trapping a player on starters", () => {
  lose("intrusul", 1);
  lose("intrusul", 2);
  lose("intrusul", 3);
  lose("intrusul", 4);

  assert.equal(scores.needsDerivedStarter("intrusul"), false);
  assert.equal(scores.scoreBoard().intrusul.nonDailyCompletions, 3);
});

test("daily results never advance attempts or mastery", () => {
  for (let day = 1; day <= 4; day += 1) {
    scores.recordScore("perechi", day === 4 ? 1_000 : 0, `zilnic ${day}`, {
      daily: `2026-08-${String(day).padStart(2, "0")}`,
    });
  }

  const record = scores.scoreBoard().perechi;
  assert.equal(record.nonDailyCompletions, 0);
  assert.equal(record.nonDailyWon, false);
  assert.equal(scores.needsDerivedStarter("perechi"), true);
});

test("bounded progress survives the recent 50-entry window", () => {
  lose("perechi", 1);
  lose("perechi", 2);
  lose("perechi", 3);
  for (let day = 1; day <= 51; day += 1) {
    scores.recordScore("perechi", 700, `zilnic ${day}`, {
      daily: `2026-${String(day).padStart(3, "0")}`,
    });
  }

  const record = scores.scoreBoard().perechi;
  assert.equal(record.recent.length, 50);
  assert.equal(record.recent.every((entry) => Boolean(entry.daily)), true);
  assert.equal(record.nonDailyCompletions, 3);
  assert.equal(record.nonDailyWon, false);
  assert.equal(scores.needsDerivedStarter("perechi"), false);

  scores.recordScore("intrusul", 100, "câștigat");
  for (let day = 1; day <= 51; day += 1) {
    scores.recordScore("intrusul", 700, `zilnic ${day}`, {
      daily: `2027-${String(day).padStart(3, "0")}`,
    });
  }
  const wonRecord = scores.scoreBoard().intrusul;
  assert.equal(wonRecord.recent.every((entry) => Boolean(entry.daily)), true);
  assert.equal(wonRecord.nonDailyWon, true);
  assert.equal(scores.needsDerivedStarter("intrusul"), false);
});

test("legacy history infers mastery without treating unknown completion as a win", () => {
  storage.setItem(
    STORAGE_KEY,
    JSON.stringify({
      intrusul: {
        best: null,
        played: 9,
        recent: [],
        completedNonDaily: true,
      },
    }),
  );
  let record = scores.scoreBoard().intrusul;
  assert.equal(record.nonDailyCompletions, 1);
  assert.equal(record.nonDailyWon, false);
  assert.equal(scores.needsDerivedStarter("intrusul"), true);

  const won = { score: 500, detail: "vechi câștigat", at: 1 };
  storage.setItem(
    STORAGE_KEY,
    JSON.stringify({
      intrusul: { best: won, played: 1, recent: [won] },
    }),
  );
  record = scores.scoreBoard().intrusul;
  assert.equal(record.nonDailyCompletions, 1);
  assert.equal(record.nonDailyWon, true);
  assert.equal(scores.needsDerivedStarter("intrusul"), false);

  const daily = { ...won, daily: "2026-07-18" };
  storage.setItem(
    STORAGE_KEY,
    JSON.stringify({
      intrusul: { best: daily, played: 1, recent: [daily] },
    }),
  );
  assert.equal(scores.needsDerivedStarter("intrusul"), true);
});

test("imports merge bounded attempts by max and mastery by OR", () => {
  lose("perechi", 1);

  const importedLosses = {
    best: { score: 0, detail: "import 1", at: 10 },
    played: 2,
    recent: [
      { score: 0, detail: "import 1", at: 10 },
      { score: 0, detail: "import 2", at: 11 },
    ],
    completedNonDaily: true,
    nonDailyCompletions: 2,
    nonDailyWon: false,
  };
  scores.importScores(JSON.stringify({ games: { perechi: importedLosses } }));
  let record = scores.scoreBoard().perechi;
  assert.equal(record.nonDailyCompletions, 2);
  assert.equal(record.nonDailyWon, false);
  assert.equal(scores.needsDerivedStarter("perechi"), true);

  scores.importScores(
    JSON.stringify({
      schema: "cat-wordgame-history-v2",
      games: {
        perechi: {
          ...importedLosses,
          best: { score: 600, detail: "import câștigat", at: 12 },
          recent: [{ score: 600, detail: "import câștigat", at: 12 }],
          nonDailyWon: true,
        },
      },
    }),
  );
  record = scores.scoreBoard().perechi;
  assert.equal(record.nonDailyCompletions, 2);
  assert.equal(record.nonDailyWon, true);
  assert.equal(scores.needsDerivedStarter("perechi"), false);

  const exported = JSON.parse(scores.exportScores());
  assert.equal(exported.schema, "cat-wordgame-history-v2");
  assert.equal(exported.games.perechi.nonDailyCompletions, 2);
  assert.equal(exported.games.perechi.nonDailyWon, true);
});

test("progress is capped and malformed storage defaults safely to starter", () => {
  storage.setItem(
    STORAGE_KEY,
    JSON.stringify({
      intrusul: {
        played: 999,
        recent: [],
        nonDailyCompletions: 999,
        nonDailyWon: false,
      },
    }),
  );
  assert.equal(scores.scoreBoard().intrusul.nonDailyCompletions, 3);
  assert.equal(scores.needsDerivedStarter("intrusul"), false);

  storage.setItem(STORAGE_KEY, "{not json");
  assert.equal(scores.needsDerivedStarter("intrusul"), true);

  storage.setItem(
    STORAGE_KEY,
    JSON.stringify({
      intrusul: {
        played: "oops",
        recent: [{}],
        nonDailyCompletions: "three",
        nonDailyWon: "yes",
      },
    }),
  );
  const record = scores.scoreBoard().intrusul;
  assert.equal(record.nonDailyCompletions, 0);
  assert.equal(record.nonDailyWon, false);
  assert.equal(scores.needsDerivedStarter("intrusul"), true);
});
