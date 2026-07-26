import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";
import ts from "typescript";

const STORAGE_KEY = "cat_wordgame_scores_v1";
const scoreSource = readFileSync(new URL("../src/scores.ts", import.meta.url), "utf8");
const homeSource = readFileSync(new URL("../src/screens/Home.tsx", import.meta.url), "utf8");
const cssSource = readFileSync(new URL("../src/styles/arcade.css", import.meta.url), "utf8");
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

function entry(score, daily, at, detail = `scor ${score}`) {
  return { score, daily, at, detail };
}

test.beforeEach(() => storage.clear());

test("daily circuit has the exact six-game product order and an empty safe default", () => {
  const circuit = scores.buildDailyCircuit({}, "2026-07-23");

  assert.deepEqual(
    circuit.games.map((game) => game.game),
    ["alchimie", "intrusul", "perechi", "conexiuni", "contexto", "lant"],
  );
  assert.equal(circuit.completed, 0);
  assert.equal(circuit.total, 0);
  assert.equal(circuit.games.every((game) => !game.completed && game.score === 0), true);
  assert.equal(Object.isFrozen(scores.DAILY_CIRCUIT_GAME_KEYS), true);

  const invalidDay = scores.buildDailyCircuit(
    { alchimie: { recent: [entry(900, "2026-07-23", 1)] } },
    "astăzi",
  );
  assert.equal(invalidDay.day, "");
  assert.equal(invalidDay.completed, 0);

  const impossibleDay = scores.buildDailyCircuit(
    { alchimie: { recent: [entry(900, "2026-02-31", 2)] } },
    "2026-02-31",
  );
  assert.equal(impossibleDay.day, "");
  assert.equal(impossibleDay.completed, 0);
});

test("zero-score runs count, best daily scores win, and every score is clamped", () => {
  const day = "2026-07-23";
  const circuit = scores.buildDailyCircuit(
    {
      alchimie: { recent: [entry(0, day, 1)] },
      intrusul: { recent: [entry(-20, day, 2)] },
      perechi: {
        recent: [
          entry(400, day, 3),
          entry(850, day, 4),
          entry(9999, "2026-07-22", 5),
        ],
      },
      conexiuni: { recent: [entry(5_000, day, 6)] },
      contexto: { best: entry(100, day, 7), recent: [] },
      lant: {
        recent: [],
        puzzles: { azi: entry(300, day, 8) },
      },
    },
    day,
  );

  assert.equal(circuit.completed, 6);
  assert.deepEqual(
    circuit.games.map((game) => game.score),
    [0, 0, 850, 1_000, 100, 300],
  );
  assert.equal(circuit.total, 2_250);
  assert.ok(circuit.total <= 6_000);
});

test("malformed and imported histories stay deterministic and local", () => {
  const day = "2026-07-23";
  const malformed = scores.buildDailyCircuit(
    {
      alchimie: { recent: [null, {}, entry("oops", day, 1), entry(500, day, 2, "")] },
      intrusul: "not a record",
      necunoscut: { recent: [entry(1_000, day, 3)] },
    },
    day,
  );
  assert.equal(malformed.completed, 0);
  assert.equal(malformed.total, 0);

  scores.importScores(
    JSON.stringify({
      games: {
        alchimie: {
          played: 1,
          recent: [entry(0, day, 4, "terminat cu zero")],
        },
        intrusul: {
          played: 1,
          recent: [entry("invalid", day, 5)],
        },
        necunoscut: {
          played: 1,
          recent: [entry(1_000, day, 6)],
        },
      },
    }),
  );
  const imported = scores.buildDailyCircuit(scores.scoreBoard(), day);
  assert.equal(imported.completed, 1);
  assert.equal(imported.total, 0);
  assert.equal(imported.games[0].completed, true);
  assert.equal(JSON.parse(storage.getItem(STORAGE_KEY)).alchimie.recent[0].score, 0);
});

test("Home renders local-only circuit actions and keeps completed rows read-only", () => {
  assert.match(homeSource, /buildDailyCircuit\(board, today\)/);
  assert.match(homeSource, /Circuitul de azi/);
  assert.match(homeSource, /Doar pe acest dispozitiv\./);
  assert.match(homeSource, /\{circuit\.completed\}\/6/);
  assert.match(homeSource, /\{circuit\.total\}\/6000 pct/);
  assert.match(homeSource, /completedToday \? "Azi ✓"/);

  const circuitMarkup = homeSource.slice(
    homeSource.indexOf('<section className="card daily-circuit"'),
    homeSource.indexOf('<div className="games-grid">'),
  );
  const helperSource = scoreSource.slice(
    scoreSource.indexOf("export function buildDailyCircuit"),
    scoreSource.indexOf("export function recentScores"),
  );
  assert.match(circuitMarkup, /if \(row\.completed\) \{/);
  assert.match(
    circuitMarkup,
    /className="daily-circuit-game-item daily-circuit-game is-complete"/,
  );
  assert.match(
    circuitMarkup,
    /aria-label=\{`\$\{game\.title\}: terminat azi, \$\{row\.score\} puncte`\}/,
  );
  assert.match(circuitMarkup, /className="daily-circuit-game daily-circuit-game-action"/);
  assert.match(circuitMarkup, /onClick=\{\(\) => openGame\(game\)\}/);
  assert.match(
    circuitMarkup,
    /aria-label=\{`Deschide \$\{game\.title\} — neterminat azi`\}/,
  );
  assert.match(circuitMarkup, /Joacă →/);
  const completedBranch = circuitMarkup.slice(
    circuitMarkup.indexOf("if (row.completed)"),
    circuitMarkup.indexOf('<li key={row.game} className="daily-circuit-game-item">'),
  );
  assert.doesNotMatch(completedBranch, /<button|onClick/);
  assert.doesNotMatch(circuitMarkup, /navigate\(/);
  assert.doesNotMatch(`${circuitMarkup}\n${helperSource}`, /fetch\(|\/api\/|telemetry|upload/i);
});

test("circuit markup exposes headings, status text, and a labelled progress list", () => {
  assert.match(
    homeSource,
    /<section className="card daily-circuit" aria-labelledby="daily-circuit-title">/,
  );
  assert.match(homeSource, /role="status"/);
  assert.match(homeSource, /aria-live="polite"/);
  assert.match(homeSource, /aria-label=\{`\$\{circuit\.completed\} din 6 jocuri terminate azi,/);
  assert.match(homeSource, /<ul className="daily-circuit-games" aria-label="Progresul jocurilor de azi">/);
  assert.match(
    homeSource,
    /aria-label=\{`\$\{game\.title\}: terminat azi, \$\{row\.score\} puncte`\}/,
  );
  assert.match(
    homeSource,
    /aria-label=\{`Deschide \$\{game\.title\} — neterminat azi`\}/,
  );
  assert.match(homeSource, /aria-label=\{`Joacă \$\{g\.title\} — \$\{/);
});

test("daily circuit CSS is mobile-first, compact, and scales to desktop", () => {
  assert.match(
    cssSource,
    /\.daily-circuit-games\s*\{[^}]*grid-template-columns: repeat\(2, minmax\(0, 1fr\)\)/s,
  );
  assert.match(cssSource, /\.daily-circuit-game\s*\{[^}]*min-height: 44px/s);
  assert.match(cssSource, /\.daily-circuit-game-name\s*\{[^}]*overflow-wrap: anywhere/s);
  assert.match(
    cssSource,
    /\.daily-circuit-game-action:focus-visible\s*\{[^}]*outline: 2px solid/s,
  );
  assert.match(
    cssSource,
    /@media \(min-width: 700px\)\s*\{[\s\S]*?\.daily-circuit-games\s*\{[^}]*repeat\(3,/,
  );
  assert.match(
    cssSource,
    /@media \(min-width: 980px\)\s*\{[\s\S]*?\.daily-circuit-games\s*\{[^}]*repeat\(6,/,
  );
});
