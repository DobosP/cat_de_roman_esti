import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";
import ts from "typescript";

const SCORE_KEY = "cat_wordgame_scores_v1";
const INVALID_IMPORT = "Fișierul ales nu este un export de istoric valid.";
const source = readFileSync(new URL("../src/scores.ts", import.meta.url), "utf8");
const compiled = ts.transpileModule(source, {
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

  removeItem(key) {
    this.values.delete(key);
  }
}

let storage;

test.beforeEach(() => {
  storage = new MemoryStorage();
  globalThis.localStorage = storage;
});

test("a first 0-point loss is history, never a record; a later win is", async () => {
  const loss = await scores.recordScoreCompletionOnce(
    "conexiuni",
    "11111111-1111-1111-1111-111111111111",
    0,
    "pierdut · 4 greșeli",
    { puzzleKey: "board-a" },
    { storage, locks: null },
  );
  assert.equal(loss.isBest, false);
  assert.equal(loss.isPuzzleBest, false);
  assert.equal(scores.bestScore("conexiuni"), null);
  assert.equal(scores.bestPuzzleScore("conexiuni", "board-a"), null);
  assert.equal(scores.timesPlayed("conexiuni"), 1);
  assert.equal(scores.recentScores("conexiuni")[0].score, 0);

  const secondLoss = scores.recordScore("conexiuni", 0, "pierdut", { puzzleKey: "board-b" });
  assert.equal(secondLoss.isBest, false);
  assert.equal(secondLoss.isPuzzleBest, false);

  const win = scores.recordScore("conexiuni", 750, "câștigat", { puzzleKey: "board-a" });
  assert.equal(win.isBest, true);
  assert.equal(win.isPuzzleBest, true);
  assert.equal(win.prev, null);
  assert.equal(scores.bestScore("conexiuni").score, 750);
  assert.equal(scores.recentScores("conexiuni").length, 3);
});

test("a saved 0-point best from an older build normalises away", () => {
  const loss = { score: 0, detail: "pierdut · 4 greșeli", at: 10 };
  storage.setItem(
    SCORE_KEY,
    JSON.stringify({ intrusul: { best: loss, played: 1, recent: [loss] } }),
  );
  let record = scores.scoreBoard().intrusul;
  assert.equal(record.best, null);
  assert.equal(record.recent.length, 1);
  assert.equal(record.recent[0].score, 0);

  const won = { score: 400, detail: "câștigat", at: 5 };
  storage.setItem(
    SCORE_KEY,
    JSON.stringify({ intrusul: { best: loss, played: 2, recent: [loss, won] } }),
  );
  record = scores.scoreBoard().intrusul;
  assert.equal(record.best.score, 400);
  assert.equal(record.best.detail, "câștigat");
  assert.equal(record.recent.length, 2);
});

test("import never revives a 0-point best", () => {
  const loss = { score: 0, detail: "pierdut", at: 10 };
  scores.importScores(
    JSON.stringify({ games: { perechi: { best: loss, played: 1, recent: [loss] } } }),
  );
  assert.equal(scores.bestScore("perechi"), null);
  assert.equal(scores.timesPlayed("perechi"), 1);
});

test("an unusable import file throws one plain Romanian message and changes nothing", () => {
  scores.recordScore("intrusul", 500, "câștigat");
  const before = storage.getItem(SCORE_KEY);
  for (const raw of ['{"games":{}}', "nu este json", "[]", '"text"']) {
    assert.throws(() => scores.importScores(raw), { message: INVALID_IMPORT }, raw);
  }
  assert.equal(storage.getItem(SCORE_KEY), before);
});
