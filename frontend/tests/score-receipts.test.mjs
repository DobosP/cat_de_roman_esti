import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";
import ts from "typescript";

const SCORE_KEY = "cat_wordgame_scores_v1";
const RECEIPTS_KEY = "_completionReceipts";
const DAY = 24 * 60 * 60 * 1_000;
const NOW = 2_000_000_000_000;
const source = readFileSync(new URL("../src/scores.ts", import.meta.url), "utf8");
const compiled = ts.transpileModule(source, {
  compilerOptions: { module: ts.ModuleKind.ESNext, target: ts.ScriptTarget.ES2021 },
}).outputText;
const scores = await import(
  `data:text/javascript;base64,${Buffer.from(compiled).toString("base64")}`
);

class MemoryStorage {
  values = new Map();
  writes = 0;

  getItem(key) {
    return this.values.get(key) ?? null;
  }

  setItem(key, value) {
    this.writes += 1;
    this.values.set(key, String(value));
  }

  removeItem(key) {
    this.values.delete(key);
  }

  clear() {
    this.values.clear();
  }
}

function rawScores() {
  return JSON.parse(storage.getItem(SCORE_KEY) || "{}");
}

function receipts() {
  return rawScores()[RECEIPTS_KEY]?.games ?? {};
}

class SerialLocks {
  names = [];
  tail = Promise.resolve();

  request(name, callback) {
    this.names.push(name);
    const result = this.tail.then(callback);
    this.tail = result.catch(() => {});
    return result;
  }
}

let storage;

test.beforeEach(() => {
  storage = new MemoryStorage();
  globalThis.localStorage = storage;
});

function complete(game, gameId, runtime = {}) {
  return scores.recordScoreCompletionOnce(
    game,
    gameId,
    700,
    `terminat ${game}`,
    { difficulty: "usor" },
    { storage, now: NOW, ...runtime },
  );
}

test("one shared lock records concurrent claims for one terminal session once", async () => {
  const locks = new SerialLocks();
  const [left, right] = await Promise.all([
    complete("contexto", "11111111-1111-1111-1111-111111111111", { locks }),
    complete("contexto", "11111111-1111-1111-1111-111111111111", { locks }),
  ]);

  assert.equal([left, right].filter(Boolean).length, 1);
  assert.equal(scores.timesPlayed("contexto"), 1);
  assert.equal(scores.recentScores("contexto").length, 1);
  assert.equal(storage.writes, 1);
  assert.deepEqual(new Set(locks.names), new Set(["cat_wordgame_scores_v1_transaction"]));
});

test("different completed IDs and different games each record under the shared lock", async () => {
  const locks = new SerialLocks();
  const outcomes = await Promise.all([
    complete("intrusul", "22222222-2222-2222-2222-222222222222", { locks }),
    complete("intrusul", "33333333-3333-3333-3333-333333333333", { locks }),
    complete("perechi", "44444444-4444-4444-4444-444444444444", { locks }),
  ]);

  assert.equal(outcomes.filter(Boolean).length, 3);
  assert.equal(scores.timesPlayed("intrusul"), 2);
  assert.equal(scores.timesPlayed("perechi"), 1);
  assert.equal(scores.recentScores().length, 3);
});

test("the no-Web-Locks fallback preserves play and deduplicates sequential reloads", async () => {
  const first = await complete("alchimie", "55555555-5555-5555-5555-555555555555", {
    locks: null,
  });
  const repeated = await complete("alchimie", "55555555-5555-5555-5555-555555555555", {
    locks: null,
  });
  const lockUnavailable = {
    request: async () => {
      throw new Error("locks disabled");
    },
  };
  const afterFailedLock = await complete(
    "alchimie",
    "66666666-6666-6666-6666-666666666666",
    { locks: lockUnavailable },
  );

  assert.ok(first);
  assert.equal(repeated, null);
  assert.ok(afterFailedLock);
  assert.equal(scores.timesPlayed("alchimie"), 2);
});

test("receipt normalization expires stale rows and rejects malformed or future rows", async () => {
  storage.setItem(SCORE_KEY, JSON.stringify({
    [RECEIPTS_KEY]: { version: 1, games: {
      lant: [
        { id: "stale-id", at: NOW - DAY },
        { id: "current-id", at: NOW - 1 },
        { id: "future-id", at: NOW + 1 },
        { id: "bad id", at: NOW - 1 },
        { id: "missing-time" },
      ],
    } },
  }));

  assert.ok(await complete("lant", "stale-id", { locks: null }));
  assert.equal(await complete("lant", "current-id", { locks: null }), null);
  const rows = receipts().lant;
  assert.deepEqual(new Set(rows.map(({ id }) => id)), new Set(["stale-id", "current-id"]));
});

test("the private receipt ledger stays capped at 1,000 rows per game", async () => {
  const rows = Array.from({ length: 1_005 }, (_, index) => ({
    id: `old-${String(index).padStart(4, "0")}`,
    at: NOW - index - 1,
  }));
  storage.setItem(SCORE_KEY, JSON.stringify({
    [RECEIPTS_KEY]: { version: 1, games: { conexiuni: rows } },
  }));

  assert.ok(await complete("conexiuni", "new-id", { locks: null }));
  const retained = receipts().conexiuni;
  assert.equal(retained.length, 1_000);
  assert.equal(retained[0].id, "new-id");
  assert.equal(new Set(retained.map(({ id }) => id)).size, 1_000);
});

test("exports and account-facing rows omit receipts; ordinary writes preserve them", async () => {
  const gameId = "77777777-7777-7777-7777-777777777777";
  await complete("perechi", gameId, { locks: null });

  const exported = scores.exportScores();
  assert.doesNotMatch(exported, new RegExp(gameId));
  assert.doesNotMatch(exported, /receipt/i);
  assert.doesNotMatch(JSON.stringify(scores.recentScores()), new RegExp(gameId));
  assert.equal(receipts().perechi[0].id, gameId);

  scores.recordScore("alchimie", 500, "ordinary write");
  assert.equal(receipts().perechi[0].id, gameId);
  scores.importScores(JSON.stringify({ games: { intrusul: {
    best: null, played: 0, recent: [], completedNonDaily: false,
    nonDailyCompletions: 0, nonDailyWon: false,
  } } }));
  assert.equal(receipts().perechi[0].id, gameId);

  scores.clearScores();
  assert.deepEqual(JSON.parse(storage.getItem(SCORE_KEY)), {});
  assert.deepEqual(receipts(), {});
});

test("a failed atomic write persists neither the score nor its receipt", async () => {
  storage.setItem(SCORE_KEY, JSON.stringify({
    contexto: {
      best: null, played: 3, recent: [], completedNonDaily: true,
      nonDailyCompletions: 3, nonDailyWon: false,
    },
  }));
  const before = storage.getItem(SCORE_KEY);
  const writesBefore = storage.writes;
  const originalSet = storage.setItem.bind(storage);
  storage.setItem = () => {
    storage.writes += 1;
    throw new Error("quota exceeded");
  };

  const outcome = await complete(
    "contexto",
    "99999999-9999-9999-9999-999999999999",
    { locks: null },
  );

  assert.ok(outcome);
  assert.equal(storage.writes, writesBefore + 1);
  assert.equal(storage.getItem(SCORE_KEY), before);
  storage.setItem = originalSet;
  assert.equal(scores.timesPlayed("contexto"), 3);
  assert.deepEqual(receipts(), {});
});

test("unavailable browser storage never blocks terminal play", async () => {
  const unavailable = {
    getItem() { throw new Error("unavailable"); },
    setItem() { throw new Error("unavailable"); },
    removeItem() { throw new Error("unavailable"); },
  };
  globalThis.localStorage = unavailable;

  const outcome = await scores.recordScoreCompletionOnce(
    "contexto",
    "88888888-8888-8888-8888-888888888888",
    900,
    "terminat",
    {},
    { storage: unavailable, locks: null, now: NOW },
  );
  assert.ok(outcome);
  assert.doesNotThrow(() => scores.clearScores());
});
