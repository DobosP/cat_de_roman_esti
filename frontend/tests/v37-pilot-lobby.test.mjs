import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

const read = (path) => readFileSync(new URL(path, import.meta.url), "utf8");
const games = read("../src/games.ts");
const home = read("../src/screens/Home.tsx");
const css = read("../src/styles/arcade.css");

test("pilot lobby keeps the provisional fun-first game order", () => {
  const legacy = new Set(["alchimie", "conexiuni", "contexto", "lant"]);
  const order = [...games.matchAll(/^\s+key: "([^"]+)",$/gm)]
    .map((match) => match[1])
    .filter((key) => legacy.has(key));
  assert.deepEqual(order, ["alchimie", "conexiuni", "contexto", "lant"]);
});

test("only Alchimie receives the terse first-play highlight", () => {
  assert.equal((games.match(/featured: true/g) ?? []).length, 1);
  assert.match(games, /key: "alchimie"[\s\S]*?featured: true/);
  assert.equal((home.match(/Începe aici/g) ?? []).length, 2);
  assert.match(home, /g\.featured \? " game-card--featured" : ""/);
  assert.match(home, /g\.featured \? "Începe aici" : g\.tag/);
  assert.match(home, /aria-label=\{`Joacă \$\{g\.title\} — \$\{g\.featured \? "Începe aici" : g\.tag\}`\}/);
  assert.match(css, /\.game-card--featured \{[\s\S]*?border-color:[\s\S]*?box-shadow:/);
  assert.doesNotMatch(`${games}\n${home}`, /boardRank|board_score|qualityScore|pilotRank/i);
});

test("first-time players see games without an empty history wall", () => {
  assert.match(home, /<section className="col history-section"[^>]*hidden=\{playedTotal === 0\}>/);
  assert.match(home, /hidden=\{playedTotal === 0\}[\s\S]*?history-tabs[\s\S]*?totals-grid[\s\S]*?<HistoryRows/);
  assert.match(home, /playedTotal === 0[\s\S]*?first-play-tools[\s\S]*?Importă istoricul/);
  assert.ok(home.indexOf("Importă istoricul") < home.indexOf("history-section"));
  assert.match(css, /\.first-play-tools button \{\s*min-height: 44px/);
  assert.match(css, /\.history-section\[hidden\] \{\s*display: none/);
});

test("the existing responsive grid keeps one-column phone cards", () => {
  assert.match(
    css,
    /\.games-grid \{[\s\S]*?grid-template-columns: repeat\(auto-fit, minmax\(min\(100%, 240px\), 1fr\)\)/,
  );
  assert.match(css, /@media \(max-width: 640px\)[\s\S]*?\.game-card \{\s*padding: 18px/);
});
