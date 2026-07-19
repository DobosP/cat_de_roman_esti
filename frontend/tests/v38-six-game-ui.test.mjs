import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

const read = (path) => readFileSync(new URL(path, import.meta.url), "utf8");
const games = read("../src/games.ts");
const app = read("../src/App.tsx");
const home = read("../src/screens/Home.tsx");
const ranking = read("../src/screens/Ranking.tsx");
const intrusulApi = read("../src/api/intrusul.ts");
const perechiApi = read("../src/api/perechi.ts");
const intrusul = read("../src/screens/Intrusul.tsx");
const perechi = read("../src/screens/Perechi.tsx");
const intrusulCss = read("../src/styles/intrusul.css");
const perechiCss = read("../src/styles/perechi.css");
const arcadeCss = read("../src/styles/arcade.css");

test("V38 lobby is six games in the tested fun-first order", () => {
  const order = [...games.matchAll(/^\s+key: "([^"]+)",$/gm)].map((match) => match[1]);
  assert.deepEqual(order, [
    "alchimie",
    "intrusul",
    "perechi",
    "conexiuni",
    "contexto",
    "lant",
  ]);
  assert.equal((games.match(/featured: true/g) ?? []).length, 1);
  assert.match(games, /key: "alchimie"[\s\S]*?featured: true/);
  assert.match(home, /Șase jocuri românești/);
  assert.match(home, /Toate cele șase jocuri/);
});

test("new game screens and their styles stay behind lazy routes", () => {
  assert.match(app, /const Intrusul = lazy\(\(\) => import\("\.\/screens\/Intrusul"\)\)/);
  assert.match(app, /const Perechi = lazy\(\(\) => import\("\.\/screens\/Perechi"\)\)/);
  assert.match(app, /path="\/intrusul"/);
  assert.match(app, /path="\/perechi"/);
  assert.match(intrusul, /import "\.\.\/styles\/intrusul\.css"/);
  assert.match(perechi, /import "\.\.\/styles\/perechi\.css"/);
});

test("personalized starts and replay fatigue use only non-daily query inputs", () => {
  for (const api of [intrusulApi, perechiApi]) {
    assert.match(api, /if \(!opts\.daily && opts\.starter !== undefined\)/);
    assert.match(api, /query\.set\("starter", opts\.starter \? "1" : "0"\)/);
    assert.match(api, /if \(!opts\.daily && opts\.previousGameId\)/);
    assert.match(api, /query\.set\("previous_game_id", opts\.previousGameId\)/);
  }
  for (const screen of [intrusul, perechi]) {
    assert.match(screen, /starter: !hasCompletedNonDaily\(GAME_KEY\)/);
    assert.match(screen, /onDaily=\{\(\) => void start\(\{ daily: todayLocal\(\) \}\)\}/);
    assert.match(screen, /onReplay=\{\(\) => void start\(\{ previousGameId: state\.game_id \}\)\}/);
  }
});

test("both boards are tap-first, compact and responsive from tiny phones to desktop", () => {
  for (const [screen, css, grid] of [
    [intrusul, intrusulCss, "intrusul-grid"],
    [perechi, perechiCss, "perechi-grid"],
  ]) {
    assert.doesNotMatch(screen, /draggable=|onDrag|onDrop/);
    assert.match(css, new RegExp(`\\.${grid} \\{[\\s\\S]*?repeat\\(2, minmax\\(0, 1fr\\)\\)`));
    assert.match(css, /@media \(min-width: 760px\)[\s\S]*?repeat\(3, minmax\(0, 1fr\)\)/);
    assert.match(css, /@media \(max-width: 339px\)[\s\S]*?grid-template-columns: minmax\(0, 1fr\)/);
    assert.match(css, /min-height: 44px/);
  }
});

test("earned feedback is short, announced and server score stays terminal-only", () => {
  assert.match(intrusul, /role="status"\s+aria-live="polite"/);
  assert.match(perechi, /role="status"\s+aria-live="polite"/);
  assert.match(intrusul, /!finished && state\.clue/);
  assert.match(perechi, /!finished && state\.hint/);
  for (const screen of [intrusul, perechi]) {
    assert.match(screen, /finished && state\.solution/);
    assert.match(screen, /score=\{state\.score\}/);
    assert.match(screen, /serverShare: state\.share/);
    assert.doesNotMatch(screen, /1_?000\s*-/);
  }
});

test("six-game ranking navigation switches to a native control on phones", () => {
  assert.match(ranking, /className="ranking-game-select"/);
  assert.match(ranking, /className="segment ranking-game-tabs"/);
  assert.match(arcadeCss, /@media \(max-width: 640px\)[\s\S]*?\.ranking-game-tabs \{ display: none; \}/);
  assert.match(arcadeCss, /\.ranking-game-select \.field \{ min-height: 44px; \}/);
});
