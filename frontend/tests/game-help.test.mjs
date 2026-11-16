import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import { existsSync, readFileSync } from "node:fs";
import path from "node:path";
import test from "node:test";
import { fileURLToPath } from "node:url";
import ts from "@typescript/typescript6";
import { GAME_HELP } from "../src/gameHelp.mjs";

const screens = {
  alchimie: "Alchimie", intrusul: "Intrusul", perechi: "Perechi",
  conexiuni: "Conexiuni", contexto: "CaldRece", lant: "Lant",
};

void test("every live game explains its choices, its ladder and how steps count", () => {
  assert.deepEqual(Object.keys(GAME_HELP).sort(), Object.keys(screens).sort());
  for (const key of Object.keys(screens)) {
    const copy = GAME_HELP[key];
    assert.deepEqual(Object.keys(copy), ["goal", "feedback", "recovery", "ladder", "steps"]);
    assert.equal(copy.ladder.length, key === "intrusul" ? 2 : 3);
    for (const text of [copy.goal, copy.feedback, copy.recovery, copy.steps, ...copy.ladder]) {
      assert.ok(text.length > 8 && text.length < 220, `${key}: keep each explanation short`);
      assert.doesNotMatch(text, /puncte|pct|scor/iu);
    }
  }
});

void test("help explains the earning rules while keeping board answers private", () => {
  assert.match(GAME_HELP.alchimie.steps, /perechile fără rezultat/);
  assert.match(GAME_HELP.perechi.goal, /legătură proprie/);
  assert.match(GAME_HELP.intrusul.feedback, /nu se potrivește/);
  assert.match(GAME_HELP.conexiuni.feedback, /Aproape: 3 din 4/);
  assert.match(GAME_HELP.contexto.feedback, /Locul 1 este cuvântul secret/);
  assert.doesNotMatch(GAME_HELP.contexto.steps, /Perfect/);
  assert.match(GAME_HELP.lant.steps, /Salturile anulate rămân numărate/);
});

void test("approved help copy and its six standalone exports remain exact", async () => {
  assert.equal(createHash("sha256").update(JSON.stringify(GAME_HELP)).digest("hex"),
    "31779113a1caf918abaf9ebf3b12b33ecc4ef40b19a1dfd188f97cb0c3296637");
  for (const key of Object.keys(screens)) {
    const record = await import(`../src/gameHelp/${key}.mjs`);
    assert.deepEqual(Object.keys(record), [`${key.toUpperCase()}_HELP`]);
    assert.equal(record[`${key.toUpperCase()}_HELP`], GAME_HELP[key]);
  }
});

const sourceRoot = fileURLToPath(new URL("../src/", import.meta.url));
function staticSourceClosure(entry) {
  const seen = new Set();
  const pending = [path.join(sourceRoot, entry)];
  while (pending.length) {
    const file = pending.pop();
    if (seen.has(file)) continue;
    seen.add(file);
    const source = ts.createSourceFile(file, readFileSync(file, "utf8"), ts.ScriptTarget.Latest, true);
    for (const statement of source.statements) {
      if (!ts.isImportDeclaration(statement) && !ts.isExportDeclaration(statement)) continue;
      if (!statement.moduleSpecifier || !ts.isStringLiteral(statement.moduleSpecifier)) continue;
      const specifier = statement.moduleSpecifier.text;
      if (!specifier.startsWith(".") || specifier.endsWith(".css")) continue;
      if (ts.isImportDeclaration(statement)) {
        const clause = statement.importClause;
        if (clause?.isTypeOnly) continue;
        if (clause && !clause.name && clause.namedBindings && ts.isNamedImports(clause.namedBindings)
          && clause.namedBindings.elements.every((item) => item.isTypeOnly)) continue;
      } else if (statement.isTypeOnly) continue;
      const base = path.resolve(path.dirname(file), specifier);
      const resolved = path.extname(base) ? base : [base + ".ts", base + ".tsx", base + ".mjs"]
        .find((candidate) => existsSync(candidate));
      assert.ok(resolved && existsSync(resolved), `Unresolved source import: ${file} -> ${specifier}`);
      pending.push(resolved);
    }
  }
  return [...seen].map((file) => path.relative(sourceRoot, file));
}

void test("each game statically owns only its own help and shared renderers own no copy", () => {
  for (const [game, name] of Object.entries(screens)) {
    const screen = game === "alchimie" ? "AlchimieChallenge" : name;
    const closure = staticSourceClosure(`screens/${screen}.tsx`);
    assert.ok(!closure.includes("gameHelp.mjs"), `${screen}: no eager compatibility aggregate`);
    assert.deepEqual(closure.filter((file) => file.startsWith("gameHelp/")), [`gameHelp/${game}.mjs`]);
  }
  for (const entry of ["components/GameHelp.tsx", "components/GameShell.tsx", "components/GameOptions.tsx",
    "screens/Home.tsx", "App.tsx"]) {
    assert.deepEqual(staticSourceClosure(entry).filter((file) => file === "gameHelp.mjs" || file.startsWith("gameHelp/")),
      [], `${entry}: no unrelated rules in its static closure`);
  }
});
