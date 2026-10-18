import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";
import { runInNewContext } from "node:vm";
import ts from "@typescript/typescript6";

const source = readFileSync(new URL("../src/alchimieMode.ts", import.meta.url), "utf8");
const code = ts.transpileModule(source, { compilerOptions: { module: ts.ModuleKind.ESNext, target: ts.ScriptTarget.ES2021 } }).outputText;
const { alchimieMode } = await import(`data:text/javascript;base64,${Buffer.from(code).toString("base64")}`);
void test("explicit exploration wins over challenge hints and a remembered challenge", () => {
  for (const query of ["", "&daily=2026-10-13", "&category=arta", "&seed=38", "&difficulty=normal"])
    for (const saved of [false, true]) assert.equal(alchimieMode("/alchimie?mode=explore" + query, saved), "explore");
});
void test("both possible default branches and every original challenge selector remain explicit", () => {
  assert.equal(alchimieMode("/alchimie", false), "explore"); assert.equal(alchimieMode("/alchimie", true), "challenges");
  for (const query of ["mode=challenges", "daily=2026-10-13", "category=", "seed=38", "difficulty=normal"])
    for (const saved of [false, true]) assert.equal(alchimieMode("/alchimie?" + query, saved), "challenges");
  assert.equal(alchimieMode("/alchimie?challenge=daily", false), "explore", "daily circuit carries the existing explicit challenges mode separately");
});

async function actualModule(relative) {
  const source = readFileSync(new URL(relative, import.meta.url), "utf8");
  const code = ts.transpileModule(source, { compilerOptions: { module: ts.ModuleKind.ESNext, target: ts.ScriptTarget.ES2021 } }).outputText;
  return import(`data:text/javascript;base64,${Buffer.from(code).toString("base64")}`);
}
const { legacyAlchimieResume } = await actualModule("../src/alchimieSavedMode.ts");
const { readExplorationSave, EXPLORATION_SAVE_KEY } = await actualModule("../src/explorationSave.ts");
void test("selector absence agrees with the unchanged exploration reader for all storage categories", () => {
  const activeKey = "cat_active_game_v1_alchimie";
  const valid = JSON.stringify({ version: 1, game_id: "collection", revision: 0, goal_id: null,
    progress: { world_id: "world", recipe_hash: "a".repeat(64), discoveries: [] } });
  const inputs = [[null, "empty"], ["", "invalid"], ["{", "invalid"], ["null", "invalid"],
    ["x".repeat(65537), "invalid"], [valid, "saved"]];
  for (const active of [null, "", "saved-challenge"]) for (const [raw, kind] of inputs) {
    const reads = [];
    const storage = { getItem(key) {
      reads.push(key);
      assert.ok(key === activeKey || key === EXPLORATION_SAVE_KEY, "selector keys must bind the existing stores");
      return key === activeKey ? active : raw;
    } };
    assert.equal(readExplorationSave(storage).kind, kind);
    reads.length = 0;
    assert.equal(legacyAlchimieResume(storage), Boolean(active) && kind === "empty");
    assert.deepEqual(reads, active ? [activeKey, EXPLORATION_SAVE_KEY] : [activeKey]);
    assert.equal(alchimieMode("/alchimie", legacyAlchimieResume(storage)), active && raw === null ? "challenges" : "explore");
  }
});
void test("selector catches unavailable storage and errors on either read without discarding exploration data", () => {
  assert.equal(legacyAlchimieResume(null), false);
  assert.equal(legacyAlchimieResume({ getItem() { throw new Error("unavailable"); } }), false);
  assert.equal(legacyAlchimieResume({ getItem(key) {
    if (key === "cat_active_game_v1_alchimie") return "saved-challenge";
    throw new Error("unavailable exploration store");
  } }), false);
  const source = readFileSync(new URL("../src/alchimieSavedMode.ts", import.meta.url), "utf8");
  const code = ts.transpileModule(source, { compilerOptions: { module: ts.ModuleKind.CommonJS } }).outputText;
  const exports = {};
  runInNewContext(code, { exports, get localStorage() { throw new Error("blocked property access"); } });
  assert.equal(exports.legacyAlchimieResume(), false);
});
