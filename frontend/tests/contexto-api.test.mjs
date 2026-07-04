import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

const source = readFileSync(new URL("../src/api/contexto.ts", import.meta.url), "utf8");

test("contexto client exposes the bounded category clue route", () => {
  assert.match(source, /export interface CategoryClue/);
  assert.match(source, /export function requestClue/);
  assert.match(source, /\/games\/\$\{encodeURIComponent\(gameId\)\}\/clue/);
  assert.match(source, /clue_available: boolean/);
});

test("clue result does not type a revealed target as part of the direct response", () => {
  const clueResult = source.match(/export interface ClueResult[\s\S]*?\n}/);
  assert.ok(clueResult);
  assert.doesNotMatch(clueResult[0], /target/);
});
