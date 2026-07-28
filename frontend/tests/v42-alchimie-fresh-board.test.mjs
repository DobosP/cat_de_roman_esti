import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

const read = (path) => readFileSync(new URL(path, import.meta.url), "utf8");
const screen = read("../src/screens/Alchimie.tsx");
const css = read("../src/styles/arcade.css");

const footer = screen.slice(
  screen.indexOf("{/* Footer actions"),
  screen.indexOf("{/* Win banner */}"),
);

test("the footer offers a fresh board without leaving the game", () => {
  assert.match(footer, /↻ Reia același joc/);
  assert.match(footer, /⚗ Alt joc/);
  assert.match(footer, /⚙ Schimbă opțiunile/);
  // "Alt joc" re-creates through the existing start() path, keeping theme + difficulty.
  assert.match(
    footer,
    /className="alchimie-other-board"[\s\S]{0,400}?void start\(\{[\s\S]{0,120}?difficulty: state\.difficulty,[\s\S]{0,120}?category: state\.board_category \?\? undefined,/,
  );
  assert.match(footer, /className="alchimie-other-board"[\s\S]{0,120}?disabled=\{busy \|\| loading\}/);
  assert.match(footer, /\{!won && \(/);
  assert.match(
    screen,
    /onReplay=\{\(\) =>\s*void start\(\{[\s\S]{0,120}?category: state\.board_category \?\? undefined,/,
  );
});

test("the new action keeps a 44px touch target", () => {
  assert.match(
    css,
    /@media \(pointer: coarse\)[\s\S]*?\.roedu-btn,[\s\S]*?min-height: 44px/,
  );
});
