import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

const read = (path) => readFileSync(new URL(path, import.meta.url), "utf8");
const api = read("../src/api/contexto.ts");
const screen = read("../src/screens/CaldRece.tsx");

test("Cald sau Rece types the server-authored recovery fields", () => {
  const rejected = api.match(/export interface GuessRejected[\s\S]*?\n}/);
  const accepted = api.match(/export interface GuessAccepted[\s\S]*?\n}/);
  assert.ok(rejected);
  assert.ok(accepted);
  assert.match(rejected[0], /suggestions: string\[\]/);
  assert.match(accepted[0], /message\?: string/);
});

test("unknown concepts become persistent recovery without a duplicate toast", () => {
  const start = screen.indexOf("if (!res.ok) {");
  const end = screen.indexOf('setText("");', start);
  assert.notEqual(start, -1);
  assert.notEqual(end, -1);
  const rejectedBranch = screen.slice(start, end);
  assert.match(
    rejectedBranch,
    /setRecovery\(\{\s*message: res\.message,\s*choices: res\.suggestions,\s*tone: "warning",/,
  );
  assert.doesNotMatch(rejectedBranch, /onToast\(res\.message/);
  assert.match(
    screen,
    /className="visually-hidden"\s+role="status"\s+aria-live="polite"[\s\S]{0,160}\{!finished \? \(recovery\?\.message \?\? ""\) : ""\}/,
  );
});

test("safe suggestions fill and focus the input but never submit", () => {
  const start = screen.indexOf("recovery.choices.map((choice)");
  const end = screen.indexOf("))}", start);
  assert.notEqual(start, -1);
  assert.notEqual(end, -1);
  const choices = screen.slice(start, end);
  assert.match(choices, /type="button"/);
  assert.match(choices, /setText\(choice\)/);
  assert.match(choices, /inputRef\.current\?\.focus\(\)/);
  assert.doesNotMatch(choices, /handleGuess|submitGuess/);
});

test("accepted autocorrection remains visible, including on a corrected win", () => {
  assert.match(
    screen,
    /if \(res\.message\) \{\s*setRecovery\(\{ message: res\.message, choices: \[\], tone: "info" \}\);/,
  );
  const result = screen.match(/<ResultCard[\s\S]*?<\/ResultCard>/);
  assert.ok(result);
  assert.match(result[0], /won && recovery\?\.message/);
  assert.match(result[0], /\{recovery\.message\}/);
});

test("recovery clears on explicit input and lifecycle transitions", () => {
  assert.match(
    screen,
    /active\.remember\(fresh\.game_id\);[\s\S]{0,160}setLatestId\(null\);\s*setText\(""\);\s*setRecovery\(null\);/,
  );
  assert.match(
    screen,
    /setCategory\(saved\.board_category \?\? null\);[\s\S]{0,160}setLatestId\(null\);\s*setText\(""\);\s*setRecovery\(null\);/,
  );
  assert.match(
    screen,
    /if \(e\.key === "Escape" && \(text \|\| recovery\)\) \{[\s\S]{0,140}setText\(""\);\s*setRecovery\(null\);/,
  );
  assert.match(screen, /const handleClue[\s\S]{0,180}setRecovery\(null\);/);
  assert.match(screen, /const handleGiveUp[\s\S]{0,180}setRecovery\(null\);/);
  assert.match(screen, /const showOptions[\s\S]{0,120}setRecovery\(null\);/);
});
