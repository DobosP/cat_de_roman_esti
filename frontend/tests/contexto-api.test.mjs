import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

const source = readFileSync(new URL("../src/api/contexto.ts", import.meta.url), "utf8");

test("contexto client exposes the bounded category clue route", () => {
  assert.match(source, /export interface CategoryClue/);
  assert.match(source, /export function requestClue/);
  assert.match(source, /\/games\/\$\{encodeURIComponent\(gameId\)\}\/clue/);
  assert.match(source, /clue_available: boolean/);
  assert.match(source, /next_clue_kind\?: NextClueKind/);
  assert.match(source, /warm_clue\?: WarmClue/);
});

test("contexto types the progressive non-target warmer clue", () => {
  const warm = source.match(/export interface WarmClue[\s\S]*?\n}/);
  const result = source.match(/export interface ClueResult[\s\S]*?\n}/);
  assert.ok(warm);
  assert.ok(result);
  assert.match(warm[0], /label: string/);
  assert.match(warm[0], /rank: number/);
  assert.match(result[0], /clue_kind: NextClueKind/);
  assert.match(result[0], /word\?: WarmClue/);
});

test("contexto guesses expose the server-authored rank field", () => {
  const guess = source.match(/export interface Guess[\s\S]*?\n}/);
  assert.ok(guess);
  assert.match(guess[0], /rank: number/);
});

test("clue result does not type a revealed target as part of the direct response", () => {
  const clueResult = source.match(/export interface ClueResult[\s\S]*?\n}/);
  assert.ok(clueResult);
  assert.doesNotMatch(clueResult[0], /target/);
});
