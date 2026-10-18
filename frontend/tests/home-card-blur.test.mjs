import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";
import ts from "@typescript/typescript6";

const source = readFileSync(new URL("../src/homeCardBlur.ts", import.meta.url), "utf8");
const code = ts.transpileModule(source, { compilerOptions: { module: ts.ModuleKind.ESNext } }).outputText;
const { homeCardBlurEnabled } = await import(`data:text/javascript;base64,${Buffer.from(code).toString("base64")}`);
void test("only valid low-memory reports opt Home cards out of their existing blur", () => {
  for (const memory of [0.25, 0.5, 1, 2]) assert.equal(homeCardBlurEnabled(memory), false);
  for (const memory of [undefined, null, 0, -1, NaN, Infinity, "2", 4, 8]) assert.equal(homeCardBlurEnabled(memory), true);
});
