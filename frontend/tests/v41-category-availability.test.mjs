import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

const read = (path) => readFileSync(new URL(path, import.meta.url), "utf8");
const meta = read("../src/api/meta.ts");
const picker = read("../src/components/CategoryPicker.tsx");
const screens = {
  conexiuni: read("../src/screens/Conexiuni.tsx"),
  contexto: read("../src/screens/CaldRece.tsx"),
  lant: read("../src/screens/Lant.tsx"),
  alchimie: read("../src/screens/Alchimie.tsx"),
};

test("category metadata types the exact game and difficulty availability matrix", () => {
  assert.match(meta, /export type Difficulty = "usor" \| "normal" \| "greu"/);
  assert.match(
    meta,
    /available_by_difficulty: Record<GameKey, Record<Difficulty, boolean>>/,
  );
});

test("the picker shows exact playable shelves and clears a stale selection", () => {
  assert.match(
    picker,
    /const visible = \(categories \?\? \[\]\)\.filter\([\s\S]*?category\.available_by_difficulty\[game\]\[difficulty\]/,
  );
  assert.match(
    picker,
    /selected\?\.available_by_difficulty\[game\]\[difficulty\]\) onInvalid\(\)/,
  );
  assert.doesNotMatch(picker, /disabled=\{/);
  assert.doesNotMatch(picker, /Indisponibil la această dificultate/);
  assert.match(picker, /chip\(null, "Toate temele", accent\)/);
});

test("all four configurable game screens bind category availability to difficulty", () => {
  for (const [game, source] of Object.entries(screens)) {
    assert.match(
      source,
      new RegExp(
        `<CategoryPicker[\\s\\S]{0,120}?game="${game}"[\\s\\S]{0,120}?difficulty=\\{difficulty\\}`,
      ),
    );
  }
});
