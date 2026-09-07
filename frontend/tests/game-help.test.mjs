import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";
import { GAME_HELP } from "../src/gameHelp.mjs";

const read = (path) => readFileSync(new URL(path, import.meta.url), "utf8");
const screens = {
  alchimie: "Alchimie", intrusul: "Intrusul", perechi: "Perechi",
  conexiuni: "Conexiuni", contexto: "CaldRece", lant: "Lant",
};

test("every live game has concise guidance for goal, feedback and recovery", () => {
  assert.deepEqual(Object.keys(GAME_HELP).sort(), Object.keys(screens).sort());
  for (const [key, screen] of Object.entries(screens)) {
    assert.deepEqual(Object.keys(GAME_HELP[key]), ["goal", "feedback", "recovery"]);
    for (const text of Object.values(GAME_HELP[key])) {
      assert.ok(text.length > 30 && text.length < 220, `${key}: keep each explanation short`);
    }
    assert.match(read(`../src/screens/${screen}.tsx`), /<GameShell[^>]*helpGame=\{GAME_KEY\}/);
  }
});

test("help explains different kinds of relationship without revealing a board answer", () => {
  assert.match(GAME_HELP.alchimie.feedback, /legăturile dintre rezultat/);
  assert.match(GAME_HELP.perechi.goal, /nu trebuie să fie sinonime/);
  assert.match(GAME_HELP.intrusul.goal, /nu aparține acelui grup/);
  assert.match(GAME_HELP.conexiuni.feedback, /Aproape: 3 din 4/);
  assert.match(GAME_HELP.contexto.feedback, /#1 este ținta/);
  assert.match(GAME_HELP.lant.feedback, /poate apropia sau ocoli/);
});

test("rules use a closed native disclosure with no session or clue side effects", () => {
  const component = read("../src/components/GameHelp.tsx");
  assert.match(component, /<details className="game-help">/);
  assert.match(component, /<summary>Reguli și ajutor<\/summary>/);
  assert.doesNotMatch(component, /\bopen=|useEffect|useState|fetch|Api|onClick|localStorage/);
  assert.match(component, /Citirea regulilor nu folosește un indiciu și nu schimbă scorul/);
});

test("earned Alchimie evidence preserves the server's oriented relationship", () => {
  const screen = read("../src/screens/Alchimie.tsx");
  const renderer = screen.slice(screen.indexOf("function EarnedLinks"), screen.indexOf("function Slot"));
  assert.match(renderer, /if \(!item\.links\?\.length\) return null/);
  assert.match(renderer, /\{link\.source\.label\} — \{link\.label\} → \{link\.target\.label\}/);
  assert.doesNotMatch(renderer, /\.parents|alchimieApi|setState|localStorage/);
  assert.match(screen, /winningReaction\?\.results\.map\(\(item\) => \(\s*<EarnedLinks/);
  assert.match(screen, /reaction\.results\.map\(\(item\) => <EarnedLinks/);
});
