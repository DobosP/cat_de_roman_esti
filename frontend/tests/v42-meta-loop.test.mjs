import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";
import ts from "typescript";

const STORAGE_KEY = "cat_wordgame_scores_v1";
const scoreSource = readFileSync(new URL("../src/scores.ts", import.meta.url), "utf8");
const homeSource = readFileSync(new URL("../src/screens/Home.tsx", import.meta.url), "utf8");
const cssSource = readFileSync(new URL("../src/styles/arcade.css", import.meta.url), "utf8");
const appSource = readFileSync(new URL("../src/App.tsx", import.meta.url), "utf8");
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

test("same-day recording is idempotent", () => {
  scores.recordScore("alchimie", 100, "azi 1", { daily: "2026-07-20" });
  scores.recordScore("intrusul", 0, "azi 2", { daily: "2026-07-20" });
  assert.equal(scores.getDailyStreak("2026-07-20"), 1);
});

test("a consecutive calendar day increments the streak", () => {
  scores.recordScore("alchimie", 100, "ziua 1", { daily: "2026-07-20" });
  scores.recordScore("perechi", 0, "ziua 2", { daily: "2026-07-21" });
  assert.equal(scores.getDailyStreak("2026-07-21"), 2);
  // Still valid the same day it landed, and while it can still be extended tomorrow.
  assert.equal(scores.getDailyStreak("2026-07-22"), 2);
});

test("a gap resets the streak to 1", () => {
  scores.recordScore("alchimie", 100, "ziua 1", { daily: "2026-07-20" });
  scores.recordScore("perechi", 0, "ziua 2", { daily: "2026-07-21" });
  scores.recordScore("conexiuni", 0, "revenire", { daily: "2026-07-25" });
  assert.equal(scores.getDailyStreak("2026-07-25"), 1);
  // Two full days without a completion since the last one reads as broken.
  assert.equal(scores.getDailyStreak("2026-07-27"), 0);
});

test("zero-score daily completions still count toward the streak", () => {
  scores.recordScore("lant", 0, "pierdut", { daily: "2026-07-20" });
  assert.equal(scores.getDailyStreak("2026-07-20"), 1);
});

test("malformed or absent streak payloads never throw and recompute conservatively", () => {
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

test("importing history never overwrites the existing local streak", () => {
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

test("imported daily rows cannot create a streak on a fresh device", () => {
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

test("export leaves the device-local streak out of portable history", () => {
  scores.recordScore("alchimie", 10, "local", { daily: "2026-07-20" });
  const exported = JSON.parse(scores.exportScores());
  assert.equal(exported.games._streak, undefined);
});

test("clearing scores also clears the local streak", () => {
  scores.recordScore("alchimie", 100, "ziua 1", { daily: "2026-07-20" });
  scores.clearScores();
  assert.equal(scores.getDailyStreak("2026-07-20"), 0);
});

test("Home shows the fire streak chip only from one day, with correct Romanian pluralization", () => {
  assert.match(homeSource, /getDailyStreak\(today\)/);
  assert.match(homeSource, /dailyStreak >= 1/);
  assert.match(
    homeSource,
    /🔥 Serie: \{dailyStreak === 1 \? "o zi" : `\$\{dailyStreak\} zile`\}/,
  );
});

// ------------------------------------------------------------------ (b) diploma de român

test("the diploma stamp renders only once the circuit is 6/6", () => {
  assert.match(homeSource, /circuit\.completed === 6 &&/);
  const diplomaBlock = homeSource.slice(
    homeSource.indexOf("circuit.completed === 6 &&"),
    homeSource.indexOf("</section>", homeSource.indexOf("circuit.completed === 6 &&")),
  );
  assert.match(diplomaBlock, /🏆 Diplomă de român/);
  assert.match(diplomaBlock, /formatDiplomaDate\(today\)/);
  assert.match(diplomaBlock, /Ai închis circuitul de azi: \{circuit\.total\} puncte\./);
  assert.match(diplomaBlock, /handleDiplomaShare/);
});

test("the diploma share text matches the specified copy and reuses the existing share/copy helpers", () => {
  assert.match(
    homeSource,
    /Cât de român ești\? Circuit 6\/6 azi · \$\{circuit\.total\} pct · Joacă: \$\{appUrl\(\)\}`/,
  );
  assert.match(homeSource, /copyResult\(text\)/);
  assert.doesNotMatch(homeSource, /fetch\(|\/api\/|telemetry|upload/i);
});

// ------------------------------------------------------------------ (c) starter chip

test("the starter chip appears on Intrusul/Perechi cards only pre-graduation", () => {
  assert.match(
    homeSource,
    /isStarterGame\(g\.key\) && needsDerivedStarter\(g\.key\) && \(/,
  );
  assert.match(homeSource, /className="faint">🌱 Nivel de început/);
  assert.match(
    homeSource,
    /function isStarterGame\(key: GameKey\): key is DerivedStarterGame \{\s*return key === "intrusul" \|\| key === "perechi";/,
  );
});

// ------------------------------------------------------------------ (d) value prop tagline

test("the hero tagline names the cultural range and keeps the h1 untouched", () => {
  assert.match(
    homeSource,
    /De la Ștefan cel Mare la Las Fierbinți: șase jocuri scurte din cultura și\s*viața românească\./,
  );
  assert.doesNotMatch(homeSource, /Șase jocuri românești\. Alege unul și intri direct în ritm\./);
  assert.match(homeSource, /aria-label="Cât de român ești\?"/);
});

// ------------------------------------------------------------------ CSS anchor

test("meta-loop CSS lives under its V42 anchor and keeps the diploma action >=44px", () => {
  assert.match(cssSource, /V42 section: meta-loop/);
  assert.match(cssSource, /@media \(pointer: coarse\)[\s\S]*?\.roedu-btn,[\s\S]*?min-height: 44px/);
  assert.match(
    cssSource,
    /\.games-grid \{[\s\S]*?repeat\(auto-fit, minmax\(min\(100%, 320px\), 1fr\)\)/,
  );
});

test("optional account controls stay outside the initial bundle graph", () => {
  assert.match(appSource, /const AccountBar = lazy\(\(\) => import\("\.\/components\/AccountBar"\)\)/);
  assert.doesNotMatch(appSource, /import AccountBar from/);
});
