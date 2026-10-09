import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

const read = (path) => readFileSync(new URL(path, import.meta.url), "utf8");
const api = read("../src/api/contexto.ts");

void test("Cald sau Rece types the server-authored recovery fields", () => {
  const rejected = api.match(/export interface GuessRejected[\s\S]*?\n}/);
  const accepted = api.match(/export interface GuessAccepted[\s\S]*?\n}/);
  assert.ok(rejected);
  assert.ok(accepted);
  assert.match(rejected[0], /suggestions: string\[\]/);
  assert.match(accepted[0], /message\?: string/);
});
