import assert from "node:assert/strict";
import test from "node:test";

import { nextActiveTileId } from "../src/perechiFocus.mjs";

void test("Perechi focus follows the next active tile and wraps in board order", () => {
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
