import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

const read = (path) => readFileSync(new URL(path, import.meta.url), "utf8");
const api = read("../src/api/contexto.ts");

void test("accepted guesses type stable ordinals and bounded server comparison kinds", () => {
  const guess = api.match(/export interface Guess[\s\S]*?\n}/);
  const feedback = api.match(/export interface GuessFeedback[\s\S]*?\n}/);
  const accepted = api.match(/export interface GuessAccepted[\s\S]*?\n}/);
  assert.ok(guess);
  assert.ok(feedback);
  assert.ok(accepted);
  assert.match(guess[0], /attempt_number: number/);
  for (const kind of ["first", "new-best", "warmer", "colder", "same", "repeat", "found"]) {
    assert.match(api, new RegExp(`(?:=|\\|) "${kind}"`));
  }
  assert.match(feedback[0], /rank_delta\?: number/);
  assert.match(accepted[0], /feedback: GuessFeedback/);
});
