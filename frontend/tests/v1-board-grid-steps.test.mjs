import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

const read = (path) => readFileSync(new URL(path, import.meta.url), "utf8");
const boards = [
  { root: ".connections-screen", grid: ".connections-grid", css: read("../src/styles/conexiuni.css") },
  { root: ".intrusul-game", grid: ".intrusul-grid", css: read("../src/styles/intrusul.css") },
  { root: ".perechi-game", grid: ".perechi-grid", css: read("../src/styles/perechi.css") },
];
const escape = (value) => value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
const columnRules = (css, grid) => [...css.matchAll(new RegExp(`${escape(grid)} \\{([^}]*)\\}`, "g"))]
  .map(([, body]) => body).filter((body) => body.includes("grid-template-columns"));

test("word boards step through 4, 2 or 1 columns and never auto-fit a ragged row", () => {
  for (const { root, grid, css } of boards) {
    assert.match(css, new RegExp(`${escape(root)} \\.game-container \\{\\s*container-type: inline-size;\\s*\\}`), root);
    const rules = columnRules(css, grid);
    assert.ok(rules.length >= 3, `${grid} declares a fallback and container steps`);
    for (const body of rules) {
      assert.doesNotMatch(body, /auto-fit|auto-fill/, grid);
      assert.match(body, /grid-template-columns: (?:repeat\((?:2|4), minmax\(0, 1fr\)\)|minmax\(0, 1fr\));/, grid);
    }
    // Browsers without container queries keep a readable two-column board.
    assert.match(rules[0], /repeat\(2, minmax\(0, 1fr\)\)/, grid);
    assert.match(css, /@container \(width < calc\(\d+(?:\.\d+)?rem \+ \d+px\)\)/, grid);
    assert.match(css, /@container \(width >= calc\(\d+(?:\.\d+)?rem \+ \d+px\)\)/, grid);
  }
});

test("quick games keep two columns below a desktop viewport", () => {
  for (const { grid, css } of boards.slice(1)) {
    assert.match(css, new RegExp(`@media \\(min-width: 760px\\) \\{\\s*@container \\(width >= calc\\(34rem \\+ \\d+px\\)\\) \\{\\s*${escape(grid)} \\{\\s*grid-template-columns: repeat\\(4`), grid);
  }
});

test("Lant stacks its route and Alchimie trades inventory columns for whole long words", () => {
  const lant = read("../src/styles/lant.css");
  assert.match(lant, /@media \(max-width: 30em\) \{\s*\.lant-route \{\s*grid-template-columns: minmax\(0, 1fr\);/);
  assert.match(lant, /@media \(max-width: 30em\)[\s\S]*?\.lant-route-arrow \{\s*transform: rotate\(90deg\);\s*justify-self: start;/);
  const alchimie = read("../src/styles/alchimie.css");
  assert.match(alchimie, /@media \(max-width: 19\.9em\) \{\s*\.alchemy-screen \.alchemy-inventory-grid \{ grid-template-columns: minmax\(0, 1fr\); \}/);
  assert.match(alchimie, /@media \(max-width: 640px\)[\s\S]*?\.alchemy-inventory-grid \{ grid-template-columns: repeat\(auto-fit, minmax\(min\(100%, max\(7rem, calc\(\(100% - 10px\) \/ 2\)\)\), 1fr\)\); \}/);
  assert.doesNotMatch(alchimie, /hyphens:/);
});
