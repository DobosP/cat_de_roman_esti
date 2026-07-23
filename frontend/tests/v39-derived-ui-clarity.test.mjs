import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

import { nextActiveTileId } from "../src/perechiFocus.mjs";

const read = (path) => readFileSync(new URL(path, import.meta.url), "utf8");
const intrusul = read("../src/screens/Intrusul.tsx");
const perechi = read("../src/screens/Perechi.tsx");
const perechiCss = read("../src/styles/perechi.css");
const resultCard = read("../src/components/ResultCard.tsx");

test("Intrusul HUD omits source difficulty that does not describe puzzle state", () => {
  assert.doesNotMatch(intrusul, /DIFFICULTY_LABEL/);
  assert.doesNotMatch(intrusul, /label="NIVEL"/);
  assert.match(intrusul, /label="ÎNCERCĂRI"/);
  assert.match(intrusul, /state\.daily && <StatBadge label="ZILNIC"/);
});

test("Perechi removes solved grid tiles but keeps earned pair history", () => {
  assert.match(perechi, /const activeTiles = state\.tiles\.filter\(\(tile\) => !tile\.solved\)/);
  assert.match(perechi, /activeTiles\.map\(\(tile\) =>/);
  assert.match(perechi, /state\.solved_pairs\.map\(\(pair\) =>/);
  assert.match(perechi, /aria-label="Perechi găsite"/);
  assert.doesNotMatch(perechi, /perechi-tile--solved/);
  assert.doesNotMatch(perechiCss, /\.perechi-tile--solved/);
});

test("Perechi focus follows the next active tile and wraps in board order", () => {
  const tiles = [
    { id: "a", solved: false },
    { id: "b", solved: true },
    { id: "c", solved: false },
    { id: "d", solved: true },
    { id: "e", solved: false },
  ];
  assert.equal(nextActiveTileId(tiles, "b"), "c");
  assert.equal(nextActiveTileId(tiles, "d"), "e");
  assert.equal(nextActiveTileId(tiles, "e"), "a");
  assert.equal(nextActiveTileId(tiles, "missing"), "a");
  assert.equal(
    nextActiveTileId(
      tiles.map((tile) => ({ ...tile, solved: true })),
      "d",
    ),
    null,
  );
});

test("Perechi moves focus only when a focused solved tile disappears", () => {
  assert.match(
    perechi,
    /focusedTileBeforeMutation\.current =\s*ids\.find\(\(id\) => tileRefs\.current\.get\(id\) === document\.activeElement\)/,
  );
  assert.match(perechi, /candidateIds\.includes\(focusedId\)/);
  assert.match(perechi, /if \(fresh\.won \|\| fresh\.lost\) \{[\s\S]*?kind: "result"/);
  assert.match(perechi, /queueFocusAfterUpdate\(result, ids\)/);
  assert.match(perechi, /tileRefs\.current\.get\(pending\.id\)/);
  assert.match(
    perechi,
    /resultFocusRef\.current\?\.querySelector<HTMLButtonElement>\("button:not\(:disabled\)"\)/,
  );
  assert.match(perechi, /target\.focus\(\)/);
});

test("daily derived results identify free play while normal replay keeps its default", () => {
  for (const screen of [intrusul, perechi]) {
    assert.match(screen, /replayLabel=\{state\.daily \? "Joacă liber →" : undefined\}/);
    assert.match(
      screen,
      /onReplay=\{\(\) => void start\(\{ previousGameId: state\.game_id \}\)\}/,
    );
  }
  assert.match(resultCard, /replayLabel = "Încă unul →"/);
});

test("UI clarity additions do not reference private derived metadata", () => {
  for (const source of [intrusul, perechi]) {
    assert.doesNotMatch(
      source,
      /source_id|catalog_id|standard_score|starter_score|standard_rank|starter_rank/,
    );
  }
});
