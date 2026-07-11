import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

const read = (path) => readFileSync(new URL(path, import.meta.url), "utf8");

const alchimie = read("../src/screens/Alchimie.tsx");
const caldRece = read("../src/screens/CaldRece.tsx");
const lant = read("../src/screens/Lant.tsx");
const conexiuni = read("../src/screens/Conexiuni.tsx");
const app = read("../src/App.tsx");

test("route presence keys the direct Suspense child so exit animations can finish", () => {
  assert.match(app, /<AnimatePresence mode="wait">\s*<Suspense\s+key=\{location\.pathname\}/);
});

test("daily games consistently carry the selected difficulty", () => {
  assert.match(
    alchimie,
    /onDaily=\{\(\) => void start\(\{ difficulty, daily: todayLocal\(\) \}\)\}/,
  );
  assert.match(
    caldRece,
    /onDaily=\{\(\) => void start\(\{ difficulty, daily: todayLocal\(\) \}\)\}/,
  );
  assert.match(
    lant,
    /onDaily=\{\(\) => void start\(\{ difficulty, daily: todayLocal\(\) \}\)\}/,
  );
  assert.match(conexiuni, /create\(\{ daily: todayLocal\(\), difficulty \}\)/);
});

test("all result screens offer immediate replay and a distinct options action", () => {
  for (const source of [alchimie, caldRece]) {
    assert.match(source, /onReplay=\{\(\) =>[\s\S]{0,180}void start\(\{/);
    assert.match(source, /onOptions=/);
  }
  assert.match(lant, /onReplay=\{\(\) => void start\(\{ difficulty: state\.difficulty \}\)\}/);
  assert.match(lant, /onOptions=/);
  assert.match(conexiuni, /onReplay=\{\(\) => void start\(\{ kind: "seed", difficulty \}\)\}/);
  assert.match(conexiuni, /onOptions=/);
});

test("Lanț reports its optimal benchmark without inventing distance after detours", () => {
  assert.doesNotMatch(lant, /state\.optimal - state\.moves/);
  assert.match(lant, /drumul optim de la start/);
  assert.match(lant, /ai atins reperul optim; ținta este încă înainte/);
});

test("Romanian-first shell copy keeps the brand and game rules truthful", () => {
  const index = read("../index.html");
  const home = read("../src/screens/Home.tsx");
  const intro = read("../src/components/GameIntro.tsx");
  const account = read("../src/components/AccountBar.tsx");
  const games = read("../src/games.ts");
  const categories = read("../src/categories.ts");
  const share = read("../src/share.ts");

  assert.match(index, /<title>Cât de român ești\?<\/title>/);
  assert.match(home, /\["Cât", "de", "român", "ești\?"\]/);
  assert.doesNotMatch(home, /330/);
  assert.match(alchimie, /ajungi\s+la ținta afișată/);
  assert.doesNotMatch(alchimie, /ținta ascunsă/i);
  assert.match(intro, /Categoria se aplică doar jocurilor libere/);
  assert.match(account, /Continuă fără cont/);
  assert.doesNotMatch(games, /à la /);
  assert.match(categories, /Viața în România/);
  assert.match(share, /`Joacă: \$\{url\}`/);
  assert.doesNotMatch(share, /lines\.push\(`Puzzle:/);
});
