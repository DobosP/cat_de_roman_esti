import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

const read = (path) => readFileSync(new URL(path, import.meta.url), "utf8");
const screen = read("../src/screens/Alchimie.tsx");
const api = read("../src/api/alchimie.ts");
const css = read("../src/styles/alchimie.css");

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
  assert.match(screen, /useState<InventoryView>\("useful"\)/);
  assert.match(screen, /const \[toolsOpen, setToolsOpen\] = useState\(false\)/);
  const toolsStart = screen.indexOf('<details className="alchemy-library-tools"');
  const toolsEnd = screen.indexOf("</details>", toolsStart);
  const tools = screen.slice(toolsStart, toolsEnd);
  assert.match(tools, /<summary>Caută și filtrează<\/summary>/);
  assert.match(tools, /aria-label="Filtrează inventarul"/);
  assert.match(tools, /type="search"/);
  assert.ok(screen.indexOf('className="alchemy-inventory-grid"') > toolsEnd);
});

test("compact search opens the full accent-insensitive encyclopedia", () => {
  assert.match(
    screen,
    /function normalizeInventorySearch[\s\S]*?normalize\("NFD"\)[\s\S]*?replace\(\/\\p\{M\}\/gu, ""\)[\s\S]*?toLocaleLowerCase\("ro-RO"\)/,
  );
  assert.match(screen, /type="search"/);
  assert.match(screen, /placeholder="Caută în toate…"/);
  assert.match(screen, /aria-label="Caută în toate conceptele descoperite"/);
  assert.match(
    screen,
    /if \(normalizedInventoryQuery\) \{[\s\S]*?normalizeInventorySearch\(item\.label\)\.includes\(normalizedInventoryQuery\)[\s\S]*?if \(inventoryView === "all"\)/,
  );
  assert.match(screen, /event\.key === "Escape" && inventoryQuery/);
  assert.match(screen, /Niciun concept găsit\./);
  assert.match(css, /\.alchemy-inventory-search[\s\S]*?min-height: 44px/);
  assert.match(
    css,
    /\.alchemy-screen \.alchemy-inventory-search \{[^}]*?width: 100%[^}]*?min-width: 0/,
  );
});

test("depleted ingredients leave the active workspace but remain in all", () => {
  assert.match(
    screen,
    /if \(inventoryView === "all"\) return true;[\s\S]*?item\.recent && !item\.depleted[\s\S]*?item\.useful && !item\.depleted/,
  );
  assert.match(screen, /disabled=\{actionsLocked \|\| won \|\| item\.depleted\}/);
  assert.match(screen, /Nu mai produce elemente noi/);
  assert.match(screen, /inventory_summary\.depleted/);
});

test("word tiles keep concise states while server readiness stays accessible", () => {
  assert.match(screen, /item\.ready[\s\S]*?gata pentru o combinație utilă/);
  assert.match(screen, /aria-label=\{accessibleLabel\}/);
  assert.match(
    screen,
    /\(isSel \|\| isFresh \|\| isTried \|\| item\.depleted\) && \([\s\S]*?<span className="alchemy-word-meta" aria-hidden="true">/,
  );
  assert.match(screen, /isSel \? "✓ Ales" : item\.depleted \? "Pus deoparte" : isTried \? "Încercat" : "✦ Nou"/);
  assert.doesNotMatch(screen, /<span aria-hidden="true">● ?<\/span>/);
  assert.match(screen, /item\.depleted[\s\S]*?\$\{item\.label\}, pus deoparte/);
});

test("combine contract exposes only bounded memory count and current retry verdict", () => {
  assert.match(api, /attempted_count: number/);
  assert.match(api, /already_tried: boolean/);
  assert.doesNotMatch(api, /attempted_pairs|attempted_partner|recipe_ids/);
});

test("inventory uses touch-sized tiles and two columns on mobile", () => {
  assert.match(css, /\.alchemy-inventory-grid \{[^}]*?repeat\(3, minmax\(0, 1fr\)\)/);
  const tileRules = [...css.matchAll(/\.alchemy-inventory-grid > \.alchemy-word \{[^}]*?min-height: (\d+)px/g)];
  assert.ok(tileRules.length >= 2, "desktop and mobile tile sizes are declared");
  for (const [, minHeight] of tileRules) assert.ok(Number(minHeight) >= 44);
  assert.match(
    css,
    /@media \(max-width: 640px\)[\s\S]*?\.alchemy-inventory-grid \{ grid-template-columns: repeat\(auto-fit, minmax\(min\(100%, max\(7rem, calc\(\(100% - 10px\) \/ 2\)\)\), 1fr\)\)/,
  );
});

test("progressive hint types keep the first hint output-only", () => {
  assert.match(api, /hint_kind: "output" \| "category" \| "pair" \| "none"/);
  assert.match(api, /hint_output: \{ label: string \} \| null/);
  assert.match(screen, /state\.hint_stage === "output"/);
  assert.match(screen, /Îți arată un rezultat apropiat/);
  const adoption = screen.slice(screen.indexOf("const applyAuthoritativeState"), screen.indexOf("const applyResumedGame"));
  assert.match(adoption, /setSelected\(fresh\.earned_hint\?\.hint\?\.slice\(0, 1\)\.map\(\(item\) => item\.id\) \?\? \[\]\)/);
  assert.match(adoption, /setHintIds\(new Set\(fresh\.earned_hint\?\.hint\?\.map/);
  assert.match(adoption, /setInventoryView\("useful"\)/);
  assert.doesNotMatch(adoption, /doCombine|alchimieApi\.combine/);
  assert.match(screen, /state\.earned_hint\.message/);
});
