import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";
import ts from "@typescript/typescript6";

const read = (path) => readFileSync(new URL(path, import.meta.url), "utf8");
const intentSource = read("../src/hooks/useDailyIntent.ts");

async function importTs(source, replacements = {}) {
  let code = ts.transpileModule(source, {
    compilerOptions: { module: ts.ModuleKind.ESNext, target: ts.ScriptTarget.ES2021 },
  }).outputText;
  for (const [from, to] of Object.entries(replacements)) code = code.replaceAll(from, to);
  return import(`data:text/javascript;base64,${Buffer.from(code).toString("base64")}`);
}

const routerStub = `data:text/javascript;base64,${Buffer.from(`
  export const useLocation = () => globalThis.__intentLocation;
  export const useNavigate = () => (to, options) => globalThis.__intentNavigations.push({ to, options });
`).toString("base64")}`;
const { useDailyIntent } = await importTs(intentSource, { '"react-router-dom"': JSON.stringify(routerStub) });

function intentAt(search, pathname = "/lant") {
  globalThis.__intentLocation = { pathname, search, hash: "" };
  globalThis.__intentNavigations = [];
  return useDailyIntent();
}

void test("the circuit intent is single-use and keeps every other query param", () => {
  const alchimie = intentAt("?mode=challenges&challenge=daily", "/alchimie");
  assert.equal(alchimie.active, true);
  alchimie.consume();
  assert.deepEqual(globalThis.__intentNavigations, [
    { to: { pathname: "/alchimie", search: "?mode=challenges", hash: "" }, options: { replace: true } },
  ]);

  const lant = intentAt("?challenge=daily");
  lant.consume();
  assert.deepEqual(globalThis.__intentNavigations[0].to, { pathname: "/lant", search: "", hash: "" });

  const free = intentAt("?mode=challenges", "/alchimie");
  assert.equal(free.active, false);
  free.consume();
  assert.deepEqual(globalThis.__intentNavigations, [], "no history write without an intent");
});

void test("daily badges show the Romanian dd.mm.yyyy date while seeds keep the raw key", async () => {
  const { displayDetail, formatDayKey, roNoun } = await importTs(read("../src/share.ts"));
  assert.equal(formatDayKey("2026-09-23"), "23.09.2026");
  // Stored details keep raw keys for dedupe; history and records show them as dd.mm.yyyy.
  assert.equal(displayDetail("4/3 salturi · 2026-09-23"), "4/3 salturi · 23.09.2026");
  assert.equal(displayDetail("câștigat · 3 greșeli"), "câștigat · 3 greșeli");
  assert.deepEqual(
    [1, 2, 19, 20, 64, 100, 101, 120].map((n) => `${n} ${roNoun(n, "salt", "salturi")}`),
    ["1 salt", "2 salturi", "19 salturi", "20 de salturi", "64 de salturi", "100 de salturi", "101 salturi", "120 de salturi"],
  );
});
