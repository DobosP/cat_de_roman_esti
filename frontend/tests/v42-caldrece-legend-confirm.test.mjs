import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

const read = (path) => readFileSync(new URL(path, import.meta.url), "utf8");
const api = read("../src/api/contexto.ts");
const screen = read("../src/screens/CaldRece.tsx");
const css = read("../src/styles/arcade.css");

test("the cold half is split into six tiers everywhere the client renders them", () => {
  const temperature = api.match(/export type Temperature =[\s\S]*?;/);
  assert.ok(temperature);
  for (const tier of ["Gasit", "Fierbinte", "Cald", "Caldut", "Rece", "Foarte rece", "Inghetat"]) {
    assert.match(temperature[0], new RegExp(`\\| "${tier}"`));
  }
  // Colour, icon and label all know the new tier, and it sits between the two
  // blues so the ramp still reads coldest-last.
  for (const map of ["TEMP_COLOR", "TEMP_ICON", "TEMP_LABEL"]) {
    const record = screen.match(new RegExp(`const ${map}: Record<Temperature, string> = \\{[\\s\\S]*?\\n\\};`));
    assert.ok(record, map);
    assert.match(record[0], /"Foarte rece": /);
    assert.ok(
      record[0].indexOf("Rece:") < record[0].indexOf('"Foarte rece":'),
      `${map} keeps Rece before Foarte rece`,
    );
    assert.ok(
      record[0].indexOf('"Foarte rece":') < record[0].indexOf("Inghetat:"),
      `${map} keeps Foarte rece before Inghetat`,
    );
  }
  assert.match(screen, /Rece: "#8ec5ff",\s*"Foarte rece": "#84bef8",\s*Inghetat: "#7bb8f2",/);
  assert.match(screen, /"Foarte rece": "Foarte rece",/);
});

test("the rank direction is explained beside the input without a help action", () => {
  const legend = screen.match(/<p id="contexto-rank-guide"[\s\S]*?<\/p>/);
  assert.ok(legend);
  assert.match(legend[0], /Un număr mai mic = mai aproape\./);
  assert.match(legend[0], /#1 este ținta\./);
  assert.match(screen, /aria-describedby="contexto-rank-guide"/);
  assert.doesNotMatch(screen, /showLegend|contexto-legend-toggle/);
  assert.ok(screen.indexOf('id="contexto-rank-guide"') < screen.indexOf('id="contexto-guess-list"'));
});

test("a fuzzy correction is offered as an explicit chip and only then costs an attempt", () => {
  const rejected = api.match(/export interface GuessRejected[\s\S]*?\n}/);
  assert.ok(rejected);
  assert.match(rejected[0], /needs_confirmation\?: true/);
  assert.match(rejected[0], /resolved_label\?: string/);
  assert.match(rejected[0], /resolved_token\?: string/);
  // The token is echoed back on the confirming request; a plain guess stays a plain body.
  assert.match(api, /export function submitGuess\(\s*gameId: string,\s*text: string,\s*confirm\?: string,\s*\)/);
  assert.match(api, /confirm \? \{ text, confirm \} : \{ text \}/);

  assert.match(screen, /confirm\?: \{ label: string; token: string \}/);
  assert.match(screen, /async \(e\?: React\.FormEvent, confirm\?: string\)/);
  assert.match(screen, /contextoApi\.submitGuess\(\s*state\.game_id,\s*q,\s*confirm,\s*\)/);
  assert.match(
    screen,
    /confirm:\s*res\.needs_confirmation && res\.resolved_label && res\.resolved_token\s*\? \{ label: res\.resolved_label, token: res\.resolved_token \}\s*: undefined,/,
  );

  const chip = screen.match(/\{recovery\.confirm \? \([\s\S]*?\) : null\}/);
  assert.ok(chip);
  assert.match(chip[0], /className="contexto-confirm-chip"/);
  assert.match(chip[0], /void handleGuess\(undefined, recovery\.confirm\?\.token\)/);
  assert.match(chip[0], /Joacă \{recovery\.confirm\.label\}/);
  assert.match(chip[0], /sau corectează textul\./);
  assert.match(css, /@media \(pointer: coarse\)[\s\S]*?\.roedu-btn,[\s\S]*?min-height: 44px/);
});

test("the typed text survives a confirmation request so it stays correctable", () => {
  // setText("") runs only on the accepted branch, after the !res.ok early return.
  const start = screen.indexOf("const handleGuess = useCallback");
  const end = screen.indexOf("const handleClue = useCallback", start);
  assert.ok(start >= 0 && end > start);
  const guess = screen.slice(start, end);
  const rejectedStart = guess.indexOf("if (!res.ok) {");
  const acceptedStart = guess.indexOf('setText("");');
  assert.ok(rejectedStart >= 0 && acceptedStart > rejectedStart);
  const rejectedBranch = guess.slice(rejectedStart, acceptedStart);
  assert.doesNotMatch(rejectedBranch, /setText\(/);
  // Once the player starts correcting it, the old label/token action disappears.
  assert.match(
    screen,
    /onChange=\{\(e\) => \{\s*setText\(e\.target\.value\);\s*setRecovery\(null\);/,
  );
});
