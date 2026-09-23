import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";
import ts from "typescript";

const read = (path) => readFileSync(new URL(path, import.meta.url), "utf8");
const intro = read("../src/components/GameIntro.tsx");
const intentSource = read("../src/hooks/useDailyIntent.ts");
const resume = read("../src/hooks/useSavedGameResume.ts");
const screens = Object.fromEntries(
  ["Intrusul", "Perechi", "Conexiuni", "CaldRece", "Alchimie", "Lant"].map((name) => [
    name,
    read(`../src/screens/${name}.tsx`),
  ]),
);

async function importTs(source, replacements = {}) {
  let code = ts.transpileModule(source, {
    compilerOptions: { module: ts.ModuleKind.ESNext, target: ts.ScriptTarget.ES2021 },
  }).outputText;
  for (const [from, to] of Object.entries(replacements)) code = code.replaceAll(from, to);
  return import(`data:text/javascript;base64,${Buffer.from(code).toString("base64")}`);
}

const routerStub = `data:text/javascript;base64,${Buffer.from(`
  export const useLocation = () => globalThis.__intentLocation;
  export const useNavigate = () => (to, options) => globalThis.__intentNavigations.push({ to, options });
`).toString("base64")}`;
const { useDailyIntent } = await importTs(intentSource, { '"react-router-dom"': JSON.stringify(routerStub) });

function intentAt(search, pathname = "/lant") {
  globalThis.__intentLocation = { pathname, search, hash: "" };
  globalThis.__intentNavigations = [];
  return useDailyIntent();
}

test("the circuit intent is single-use and keeps every other query param", () => {
  const alchimie = intentAt("?mode=challenges&challenge=daily", "/alchimie");
  assert.equal(alchimie.active, true);
  alchimie.consume();
  assert.deepEqual(globalThis.__intentNavigations, [
    { to: { pathname: "/alchimie", search: "?mode=challenges", hash: "" }, options: { replace: true } },
  ]);

  const lant = intentAt("?challenge=daily");
  lant.consume();
  assert.deepEqual(globalThis.__intentNavigations[0].to, { pathname: "/lant", search: "", hash: "" });

  const free = intentAt("?mode=challenges", "/alchimie");
  assert.equal(free.active, false);
  free.consume();
  assert.deepEqual(globalThis.__intentNavigations, [], "no history write without an intent");
});

test("GameIntro consumes the intent from both start buttons and swaps only their order", () => {
  assert.match(intro, /import \{ useDailyIntent \} from "\.\.\/hooks\/useDailyIntent";/);
  assert.doesNotMatch(intro, /location\.search/);
  assert.match(intro, /const dailyFirst = Boolean\(onDaily\) && intent\.active;/);
  assert.match(intro, /const consumeThen = \(action\?: \(\) => void\) => \(\) => \{\s*intent\.consume\(\);\s*action\?\.\(\);\s*\};/);
  assert.match(intro, /<Button autoFocus onClick=\{consumeThen\(dailyFirst \? onDaily : onStart\)\}/);
  assert.match(intro, /variant="secondary"\s*onClick=\{consumeThen\(dailyFirst \? onStart : onDaily\)\}/);
  assert.equal(intro.match(/onClick=\{consumeThen\(/g)?.length, 2);
});

test("resuming a saved free round from the circuit tells the player the daily still waits", () => {
  assert.match(resume, /onDailyBypassed\?: \(\) => void;/);
  assert.match(resume, /if \(!dailyIntent\.active\) return false;/);
  // Only today's daily uses up the intent; an older day's daily keeps it silently.
  assert.match(
    resume,
    /if \(daily === todayLocal\(\)\) dailyIntent\.consume\(\);\s*else if \(!daily && !terminal && onDailyBypassed\) \{\s*onDailyBypassed\(\);\s*return true;/,
  );
  // The bypass is decided first so the screen can skip its own "Joc reluat." toast.
  assert.match(
    resume,
    /const bypassed = dailyResumeRef\.current\(\(state as \{ daily\?: unknown \}\)\.daily, detail\.terminal\);\s*onResume\(state, \{ \.\.\.detail, bypassed \}\);/,
  );
  for (const name of ["Alchimie", "CaldRece", "Conexiuni", "Lant"]) {
    assert.match(screens[name], /if \(!terminal && !bypassed\) onToast\("Joc reluat\.", "info"\);/, name);
  }
  for (const [name, screen] of Object.entries(screens)) {
    assert.match(
      screen,
      /onDailyBypassed: \(\) => onToast\("Ai continuat jocul liber început\. Provocarea zilei te așteaptă după ce îl termini\.", "info"\),/,
      name,
    );
  }
});

test("Intrusul and Perechi free results lead back to today's unfinished circuit daily", () => {
  for (const name of ["Intrusul", "Perechi"]) {
    const screen = screens[name];
    assert.match(
      screen,
      /!buildDailyCircuit\(scoreBoard\(\), todayLocal\(\)\)\.games\.find\(\(g\) => g\.game === GAME_KEY\)\?\.completed/,
      name,
    );
    // The latch keeps the offer after a failed create; a started round clears it.
    assert.match(
      screen,
      /const offerDaily = \(dailyIntent\.active \|\| dailyRetry\) && dailyPending && state\?\.daily !== todayLocal\(\);/,
      name,
    );
    assert.match(
      screen,
      /offerDaily\s*\? \(\) => \{\s*setDailyRetry\(true\);\s*dailyIntent\.consume\(\);\s*void start\(\{ daily: todayLocal\(\) \}\);\s*\}/,
      name,
    );
    assert.match(screen, /setState\(fresh\);\s*setDailyRetry\(false\);/, name);
    assert.match(screen, /replayLabel=\{offerDaily \? "Joacă provocarea zilei →" : state\.daily \? "Joacă liber →" : undefined\}/, name);
  }
});

test("daily badges show the Romanian dd.mm.yyyy date while seeds keep the raw key", async () => {
  const { displayDetail, formatDayKey, roNoun } = await importTs(read("../src/share.ts"));
  assert.equal(formatDayKey("2026-09-23"), "23.09.2026");
  // Stored details keep raw keys for dedupe; history and records show them as dd.mm.yyyy.
  assert.equal(displayDetail("4/3 salturi · 2026-09-23"), "4/3 salturi · 23.09.2026");
  assert.equal(displayDetail("câștigat · 3 greșeli"), "câștigat · 3 greșeli");
  assert.deepEqual(
    [1, 2, 19, 20, 64, 100, 101, 120].map((n) => `${n} ${roNoun(n, "salt", "salturi")}`),
    ["1 salt", "2 salturi", "19 salturi", "20 de salturi", "64 de salturi", "100 de salturi", "101 salturi", "120 de salturi"],
  );
  assert.match(screens.Intrusul, /label="ZILNIC" value=\{formatDayKey\(state\.daily\)\}/);
  assert.match(screens.Perechi, /label="ZILNIC" value=\{formatDayKey\(state\.daily\)\}/);
  assert.match(screens.Conexiuni, /label="ZILNIC" value=\{formatDayKey\(state\.daily\)\}/);
  assert.match(screens.CaldRece, /`📅 \$\{formatDayKey\(state\.daily\)\}`/);
  assert.match(screens.Alchimie, /\{state\.daily && ` · \$\{formatDayKey\(state\.daily\)\}`\}/);
  assert.match(screens.Lant, /` Provocarea zilei: \$\{formatDayKey\(state\.daily\)\}\.`/);
  for (const [name, screen] of Object.entries(screens)) {
    assert.match(screen, /daily-\$\{state\.daily\}/, `${name} keeps the raw daily key in its puzzle key`);
    assert.doesNotMatch(screen, /formatDayKey\(todayLocal\(\)\)|\bazi\b[^"\n]*formatDayKey/, name);
  }
});
