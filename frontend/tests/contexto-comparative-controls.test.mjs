import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

const read = (path) => readFileSync(new URL(path, import.meta.url), "utf8");
const api = read("../src/api/contexto.ts");
const screen = read("../src/screens/CaldRece.tsx");
const css = read("../src/styles/arcade.css");

test("accepted guesses type stable ordinals and bounded server comparison kinds", () => {
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

test("Bune and Recente use server rank order and stable attempt ordinals", () => {
  assert.match(screen, /type GuessView = "best" \| "recent"/);
  assert.match(screen, /right\.attempt_number - left\.attempt_number/);
  assert.match(screen, /role="tablist"/);
  assert.match(screen, />\s*Bune\s*</);
  assert.match(screen, />\s*Recente\s*</);
  assert.match(screen, /displayedGuesses\.map\(\(g\)/);
  assert.match(css, /\.contexto-guess-tabs button \{[\s\S]*?min-height: 44px/);
});

test("the latest accepted guess renders exactly one server-authored comparison", () => {
  assert.match(screen, /setFeedback\(res\.feedback\)/);
  assert.match(screen, /className=\{`contexto-comparison contexto-comparison--\$\{feedback\.kind\}`\}/);
  assert.match(screen, /\{feedback\.message\}/);
  assert.match(screen, /role="status"/);
  assert.match(css, /\.contexto-comparison \{[\s\S]*?min-height: 44px/);
});

test("guess form owns a compact phone-safe clue reveal options row", () => {
  const form = screen.indexOf('<form onSubmit={handleGuess} className="row contexto-input-bar"');
  const actions = screen.indexOf('className="contexto-action-row"', form);
  const hudEnd = screen.indexOf("</Hud>");
  assert.ok(form > hudEnd);
  assert.ok(actions > form);
  assert.match(screen, /\{clueActionLabel\}/);
  assert.match(screen, /`Indiciu în \$\{clueCountdown\}`/);
  assert.match(css, /\.contexto-action-row \{[\s\S]*?repeat\(3, minmax\(0, 1fr\)\)/);
  assert.match(css, /\.contexto-action-row \.roedu-btn,[\s\S]*?min-height: 44px/);
});

test("reveal requires an inline confirmation and the first tap cannot call giveup", () => {
  const firstTapStart = screen.indexOf("const requestRevealConfirmation");
  const firstTapEnd = screen.indexOf("const showOptions", firstTapStart);
  const firstTap = screen.slice(firstTapStart, firstTapEnd);
  assert.match(firstTap, /setConfirmReveal\(true\)/);
  assert.doesNotMatch(firstTap, /contextoApi\.giveUp/);
  assert.match(screen, /Arătăm răspunsul\?/);
  assert.match(screen, /Da, arată/);
  assert.match(screen, /onClick=\{\(\) => void handleGiveUp\(\)\}/);
  assert.match(screen, /const handleGiveUp[\s\S]*?contextoApi\.giveUp\(state\.game_id\)/);
});

test("guess, clue, and game lifecycle dismiss an armed reveal", () => {
  const clears = screen.match(/setConfirmReveal\(false\)/g) ?? [];
  assert.ok(clears.length >= 10);
  assert.match(screen, /const handleGuess[\s\S]*?setConfirmReveal\(false\)/);
  assert.match(screen, /const handleClue[\s\S]*?setConfirmReveal\(false\)/);
  assert.match(screen, /active\.remember\(fresh\.game_id\);[\s\S]*?setConfirmReveal\(false\)/);
  assert.match(screen, /const showOptions[\s\S]*?setConfirmReveal\(false\)/);
  assert.match(screen, /onChange=\{\(e\) => \{[\s\S]*?setText\(e\.target\.value\);[\s\S]*?setConfirmReveal\(false\)/);
  assert.match(screen, /setText\(choice\);\s*setConfirmReveal\(false\)/);
  assert.match(screen, /setText\(word\);\s*setConfirmReveal\(false\)/);
});
