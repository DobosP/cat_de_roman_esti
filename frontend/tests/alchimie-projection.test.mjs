import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

const read = (path) => readFileSync(new URL(path, import.meta.url), "utf8");
const screen = read("../src/screens/Alchimie.tsx");
const api = read("../src/api/alchimie.ts");
const css = read("../src/styles/arcade.css");

test("inventory offers short recent/useful/all views from server metadata", () => {
  assert.match(api, /recent: boolean/);
  assert.match(api, /useful: boolean/);
  assert.match(api, /ready: boolean/);
  assert.match(api, /depleted: boolean/);
  assert.match(screen, /type InventoryView = "recent" \| "useful" \| "all"/);
  assert.match(screen, /recent: "Recente"/);
  assert.match(screen, /useful: "Utile"/);
  assert.match(screen, /all: "Toate"/);
  assert.match(screen, /role="group"/);
  assert.match(screen, /aria-pressed=\{inventoryView === view\}/);
  assert.doesNotMatch(screen, /role="tab(?:list)?"/);
  assert.match(screen, /visibleInventory\.map/);
});

test("depleted ingredients leave the active workspace but remain in all", () => {
  assert.match(
    screen,
    /if \(inventoryView === "all"\) return true;[\s\S]*?item\.recent && !item\.depleted[\s\S]*?item\.useful && !item\.depleted/,
  );
  assert.match(screen, /disabled=\{won \|\| busy \|\| item\.depleted\}/);
  assert.match(screen, /Nu mai produce elemente noi/);
  assert.match(screen, /inventory_summary\.depleted/);
});

test("ready markers explain their meaning without polluting accessible names", () => {
  assert.match(screen, /item\.ready[\s\S]*?gata pentru o combinație utilă/);
  assert.match(screen, /aria-label=\{accessibleLabel\}/);
  assert.match(screen, /<span aria-hidden="true">● <\/span>/);
  assert.match(screen, /item\.depleted[\s\S]*?\$\{item\.label\}, pus deoparte/);
});

test("mobile inventory is a two-column 44px chip grid", () => {
  assert.match(css, /\.alchemy-inventory-grid[\s\S]*?minmax\(128px, 1fr\)/);
  assert.match(css, /\.alchemy-inventory-grid > \.chip[\s\S]*?min-height: 44px/);
  assert.match(
    css,
    /@media \(max-width: 640px\)[\s\S]*?\.alchemy-inventory-grid[\s\S]*?repeat\(2, minmax\(0, 1fr\)\)/,
  );
});

test("progressive hint types keep the first hint output-only", () => {
  assert.match(api, /hint_kind: "output" \| "category" \| "pair" \| "none"/);
  assert.match(api, /hint_output: \{ label: string \} \| null/);
  assert.match(screen, /state\.hint_stage === "output"/);
  assert.match(screen, /Îți arată un rezultat apropiat/);
  assert.match(
    screen,
    /if \(res\.hint\)[\s\S]*?setInventoryView\("useful"\)[\s\S]*?setSelected\(ids\)/,
  );
  assert.match(screen, /else \{[\s\S]*?setHintIds\(new Set\(\)\);[\s\S]*?setInventoryView\("useful"\)/);
});
