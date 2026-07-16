import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

const read = (path) => readFileSync(new URL(path, import.meta.url), "utf8");
const api = read("../src/api/lant.ts");
const screen = read("../src/screens/Lant.tsx");

test("Lanț client preserves bounded server recovery fields", () => {
  const move = api.match(/export interface MoveResult[\s\S]*?\n}/);
  const hint = api.match(/export interface HintResult[\s\S]*?\n}/);
  assert.ok(move);
  assert.ok(hint);
  assert.match(move[0], /message\?: string/);
  assert.match(move[0], /dead_end\?: boolean/);
  assert.match(move[0], /suggestions\?: string\[\]/);
  assert.match(hint[0], /alternatives_labels\?: string\[\]/);
});

test("Lanț keeps move recovery visible and exposes fuzzy spelling choices", () => {
  assert.match(screen, /choices: res\.suggestions \?\? \[\]/);
  assert.match(screen, /tone: res\.dead_end \? "warning" : "info"/);
  assert.match(
    screen,
    /className="visually-hidden"\s+role="status"\s+aria-live="polite"[\s\S]{0,120}\{recovery\?\.message \?\? ""\}/,
  );
  assert.match(screen, /recovery\.tone === "warning" \? "⚠" : "ℹ"/);
  assert.match(screen, /recovery\.choices\.map\(\(choice\)/);
  assert.match(screen, /setText\(choice\)/);
  assert.doesNotMatch(
    screen,
    /choices: res\.suggestions \?\? \[\],[\s\S]{0,80}onToast\(message/,
  );
  assert.doesNotMatch(
    screen,
    /setRecovery\(\{ message, choices: \[\], tone: "warning" \}\);\s+onToast\(message/,
  );
});

test("Lanț preserves an autocorrection message when the corrected hop wins", () => {
  const result = screen.match(/<ResultCard[\s\S]*?<\/ResultCard>/);
  assert.ok(result);
  assert.match(result[0], /recovery\?\.message/);
});

test("Lanț second-stage hints render named alternatives as keyboard buttons", () => {
  assert.match(screen, /hint\.alternatives_labels\?\.length/);
  assert.match(screen, /hint\.alternatives_labels\.map\(\(label\)/);
  assert.match(screen, /setText\(label\)/);
});
