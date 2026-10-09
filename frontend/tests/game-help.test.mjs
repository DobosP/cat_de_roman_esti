import assert from "node:assert/strict";
import test from "node:test";
import { GAME_HELP } from "../src/gameHelp.mjs";

const screens = {
  alchimie: "Alchimie", intrusul: "Intrusul", perechi: "Perechi",
  conexiuni: "Conexiuni", contexto: "CaldRece", lant: "Lant",
};

void test("every live game has concise guidance for goal, feedback and recovery", () => {
  assert.deepEqual(Object.keys(GAME_HELP).sort(), Object.keys(screens).sort());
  for (const [key] of Object.entries(screens)) {
    assert.deepEqual(Object.keys(GAME_HELP[key]), ["goal", "feedback", "recovery"]);
    for (const text of Object.values(GAME_HELP[key])) {
      assert.ok(text.length > 30 && text.length < 220, `${key}: keep each explanation short`);
    }
  }
});

void test("help explains different kinds of relationship without revealing a board answer", () => {
  assert.match(GAME_HELP.alchimie.feedback, /legăturile dintre rezultat/);
  assert.match(GAME_HELP.perechi.goal, /nu trebuie să fie sinonime/);
  assert.match(GAME_HELP.intrusul.goal, /nu aparține acelui grup/);
  assert.match(GAME_HELP.conexiuni.feedback, /Aproape: 3 din 4/);
  assert.match(GAME_HELP.contexto.feedback, /#1 este ținta/);
  assert.match(GAME_HELP.lant.feedback, /poate apropia sau ocoli/);
});
