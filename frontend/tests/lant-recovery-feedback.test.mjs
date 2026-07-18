import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

const read = (path) => readFileSync(new URL(path, import.meta.url), "utf8");
const api = read("../src/api/lant.ts");
const screen = read("../src/screens/Lant.tsx");

test("Lanț client preserves bounded server recovery fields", () => {
  const choice = api.match(/export interface LantChoice[\s\S]*?\n}/);
  const progress = api.match(/export interface LantProgress[\s\S]*?\n}/);
  const state = api.match(/export interface LantState[\s\S]*?\n}/);
  const move = api.match(/export interface MoveResult[\s\S]*?\n}/);
  const hint = api.match(/export interface HintResult[\s\S]*?\n}/);
  assert.ok(choice);
  assert.ok(progress);
  assert.ok(state);
  assert.ok(move);
  assert.ok(hint);
  assert.match(choice[0], /label: string/);
  assert.match(choice[0], /relation: string/);
  assert.doesNotMatch(choice[0], /id:/);
  assert.match(progress[0], /kind: LantProgressKind/);
  assert.match(progress[0], /message: string/);
  assert.match(state[0], /choices: LantChoice\[\]/);
  assert.match(state[0], /backtrack_recommended: boolean/);
  assert.match(move[0], /message\?: string/);
  assert.match(move[0], /dead_end\?: boolean/);
  assert.match(move[0], /suggestions\?: string\[\]/);
  assert.match(move[0], /choices\?: LantChoice\[\]/);
  assert.match(move[0], /progress\?: LantProgress/);
  assert.match(move[0], /backtrack_recommended\?: boolean/);
  assert.match(
    hint[0],
    /stage\?: "direction" \| "alternatives" \| "hop" \| "backtrack"/,
  );
  assert.match(hint[0], /alternatives_labels\?: string\[\]/);
  assert.match(hint[0], /alternatives_choices\?: LantChoice\[\]/);
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

test("Lanț renders local relation chips and keeps free typing available", () => {
  assert.match(screen, /label: "Alege o legătură"/);
  assert.match(screen, /state\.choices\.map\(\(choice\)/);
  assert.match(screen, /className="lant-choice"/);
  assert.match(screen, /onClick=\{\(\) => void submit\(choice\)\}/);
  assert.match(screen, /toate sunt legături valide/);
  assert.match(screen, /placeholder="Sau scrie alt concept…"/);
});

test("Lanț renders coarse move progress and highlights recommended undo", () => {
  assert.match(screen, /const PROGRESS_ICON/);
  assert.match(screen, /className=\{"lant-progress lant-progress--" \+ progress\.kind\}/);
  assert.match(screen, /<strong>\{progress\.message\}<\/strong>/);
  assert.match(screen, /role="status"/);
  assert.match(screen, /res\.backtrack_recommended \?\? prev\.backtrack_recommended/);
  assert.match(screen, /lant-undo--recommended/);
  assert.match(screen, /Înapoi · recomandat/);
});

test("Lanț renders progressive direction, alternatives, and one-hop help", () => {
  assert.match(screen, /hint\.stage === "direction"/);
  assert.match(screen, /hint\.stage === "alternatives"/);
  assert.match(screen, /hint\.alternatives_choices\?\.length/);
  assert.match(screen, /hint\.alternatives_choices\.map\(\(choice\)/);
  assert.match(screen, /if \(hint\.hint\) setText\(hint\.hint\.label\)/);
  assert.match(screen, /res\.hint \|\| res\.stage/);
  assert.match(screen, /VARIANTE UTILE/);
  assert.match(screen, /\? "💡 Mai clar"/);
  assert.doesNotMatch(screen, /DOUĂ VARIANTE/);
});

test("Lanț turns revisit traps into an explicit free-undo action", () => {
  assert.match(screen, /hint\.stage === "backtrack"/);
  assert.match(screen, /UN PAS ÎNAPOI/);
  assert.match(screen, /Anulează ultimul salt/);
  assert.match(screen, /onClick=\{\(\) => void handleUndo\(\)\}/);
});

test("Lanț recovery fills focus only fine pointers", () => {
  assert.match(
    screen,
    /const focusInputForFinePointer = useCallback[\s\S]*?matchMedia\("\(pointer: fine\)"\)\.matches[\s\S]*?inputRef\.current\?\.focus\(\)/,
  );
  assert.match(
    screen,
    /const fresh = await undoLant\(state\.game_id\);[\s\S]{0,160}focusInputForFinePointer\(\)/,
  );
  assert.equal(
    screen.match(/inputRef\.current\?\.focus\(\)/g)?.length,
    1,
    "only the fine-pointer helper may call focus directly",
  );
  assert.match(
    screen,
    /recovery\.choices\.map[\s\S]*?setText\(choice\);[\s\S]*?focusInputForFinePointer\(\)/,
  );
  assert.match(
    screen,
    /hint\.alternatives_choices\.map[\s\S]*?setText\(choice\.label\);[\s\S]*?focusInputForFinePointer\(\)/,
  );
  assert.match(
    screen,
    /if \(hint\.hint\) setText\(hint\.hint\.label\);[\s\S]*?focusInputForFinePointer\(\)/,
  );
});
