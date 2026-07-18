import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

const screen = readFileSync(
  new URL("../src/screens/CaldRece.tsx", import.meta.url),
  "utf8",
);

test("Cald sau Rece labels the next server-authored clue stage", () => {
  assert.match(screen, /state\?\.next_clue_kind === "warmer" \? "Mai cald" : "Indiciu"/);
  assert.match(screen, /Arată un cuvânt sigur mai cald/);
  assert.match(screen, /Nu mai există un indiciu sigur/);
  assert.match(screen, /const res = await contextoApi\.requestClue\(state\.game_id\)/);
  assert.match(screen, /setState\(res\)/);
});

test("compact clue cards keep category and warmer word visible on mobile", () => {
  assert.match(screen, /\(state\?\.clue \|\| state\?\.warm_clue\) && !finished/);
  assert.match(screen, /🧭 Categorie/);
  assert.match(screen, /🔥 Încearcă/);
  assert.match(screen, /\{state\.warm_clue\.label\}/);
  assert.match(screen, /#\{state\.warm_clue\.rank\}/);
  assert.match(screen, /aria-label="Indicii folosite"/);
});

test("guess responses retain progressive clue state from the server", () => {
  const nextKindUpdates = screen.match(/next_clue_kind: res\.next_clue_kind/g) ?? [];
  const warmUpdates = screen.match(/warm_clue: res\.warm_clue \?\? prev\.warm_clue/g) ?? [];
  assert.equal(nextKindUpdates.length, 2);
  assert.equal(warmUpdates.length, 2);
});

test("a rejected stale clue refreshes authoritative availability", () => {
  assert.match(screen, /err instanceof ApiError && err\.status === 400/);
  assert.match(screen, /setState\(await contextoApi\.getGame\(state\.game_id\)\)/);
});
