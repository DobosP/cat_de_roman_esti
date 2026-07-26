import assert from "node:assert/strict";
import test from "node:test";

import {
  acquireFlight,
  recoverAuthoritative,
  releaseFlight,
} from "../src/asyncControl.mjs";

test("single-flight acquisition is synchronous and reusable after release", () => {
  const lock = { current: false };
  assert.equal(acquireFlight(lock), true);
  assert.equal(lock.current, true);
  assert.equal(acquireFlight(lock), false);
  releaseFlight(lock);
  assert.equal(lock.current, false);
  assert.equal(acquireFlight(lock), true);
});

test("authoritative recovery returns a committed terminal state", async () => {
  const terminal = { game_id: "g1", won: true, lost: false, score: 800 };
  const recovered = await recoverAuthoritative(async () => terminal);
  assert.deepEqual(recovered, { ok: true, value: terminal });
});

test("failed recovery never invents or reuses a stale state", async () => {
  const recovered = await recoverAuthoritative(async () => {
    throw new Error("offline");
  });
  assert.deepEqual(recovered, { ok: false, value: null });
});
