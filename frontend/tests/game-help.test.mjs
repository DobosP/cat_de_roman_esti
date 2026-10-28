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

void test("separate help records preserve every original text and the public aggregate", async () => {
  // Preserve the original aggregate pin for the 16 unchanged texts; only the
  // two Alchimie control instructions are intentionally revised by ADR-0222.
  // A separate exact record pin below binds the current Alchimie guidance.
  const historicalHelp = {
    ...GAME_HELP,
    alchimie: {
      ...GAME_HELP.alchimie,
      feedback: "După o descoperire, citește legăturile dintre rezultat și cele două concepte. Ele explică asocierea.",
      recovery: "Dacă nu apare nimic nou, schimbă un concept. „Utile” arată ce mai poate contribui; cere un indiciu când devine disponibil.",
    },
  };
  assert.equal(createHash("sha256").update(JSON.stringify(GAME_HELP.alchimie)).digest("hex"),
    "8f259cc7c1838c0406234b3e59352ac6bcef4475ecd9b9cab807125bffd06c33");
  assert.equal(createHash("sha256").update(JSON.stringify(historicalHelp)).digest("hex"),
    "b8ac05ddf1c8d448b247d391358ff055624b246379d4981fef22e8374075504e");
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
    "screens/Home.tsx", "screens/AlchimieExplore.tsx", "App.tsx"]) {
    assert.deepEqual(staticSourceClosure(entry).filter((file) => file === "gameHelp.mjs" || file.startsWith("gameHelp/")),
      [], `${entry}: no unrelated rules in its static closure`);
  }
});
