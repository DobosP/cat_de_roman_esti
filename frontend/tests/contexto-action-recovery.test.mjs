import assert from "node:assert/strict";
import test from "node:test";
import { createContextoActionOwner, recoverOwnedContextoAction } from "../src/contextoActionRecovery.mjs";

function pointer(initial = "game-a") {
  let value = initial;
  return {
    peek: () => value,
    isCurrent: (id) => value === id,
    set: (id) => { value = id; },
  };
}

function deferred() {
  let resolve;
  let reject;
  const promise = new Promise((yes, no) => { resolve = yes; reject = no; });
  return { promise, resolve, reject };
}

test("one frozen ticket owns the action and an unrelated finish cannot release it", () => {
  const owner = createContextoActionOwner(pointer());
  const ticket = owner.begin("game-a");
  assert.ok(ticket);
  assert.throws(() => { ticket.gameId = "other"; }, TypeError);
  assert.equal(owner.begin("game-a"), null);
  assert.equal(owner.finish({ gameId: "game-a", savedId: "game-a" }), false);
  assert.equal(owner.hasPending(), true);
  assert.equal(owner.owns(ticket), true);
  assert.equal(owner.finish(ticket), true);
  assert.equal(owner.hasPending(), false);
  assert.ok(owner.begin("game-a"));
});

test("a successful recovery performs one read and returns the exact authoritative state", async () => {
  const owner = createContextoActionOwner(pointer());
  const ticket = owner.begin("game-a");
  const state = { game_id: "game-a", won: true, guesses: [{ id: "earned" }], score: 900 };
  let reads = 0;
  const result = await recoverOwnedContextoAction(owner, ticket, async (id) => {
    reads += 1;
    assert.equal(id, "game-a");
    return state;
  });
  assert.deepEqual(result, { kind: "recovered", state });
  assert.equal(result.state, state);
  assert.equal(reads, 1);
  assert.equal(owner.hasPending(), true); // The caller still owns adoption and cleanup.
});

test("a failed read has no stale substitute or automatic retry", async () => {
  const owner = createContextoActionOwner(pointer());
  const ticket = owner.begin("game-a");
  let reads = 0;
  const result = await recoverOwnedContextoAction(owner, ticket, async () => {
    reads += 1;
    throw new Error("offline");
  });
  assert.deepEqual(result, { kind: "failed" });
  assert.equal(reads, 1);
});

test("an owned missing-session read is classified without changing the pointer", async () => {
  const active = pointer();
  const owner = createContextoActionOwner(active);
  const ticket = owner.begin("game-a");
  const result = await recoverOwnedContextoAction(owner, ticket, async () => {
    throw { status: 404 };
  }, (error) => error.status === 404);
  assert.deepEqual(result, { kind: "missing" });
  assert.equal(active.peek(), "game-a");
});

test("unmount or cancellation suppresses a late successful read", async () => {
  const owner = createContextoActionOwner(pointer());
  const ticket = owner.begin("game-a");
  const held = deferred();
  const result = recoverOwnedContextoAction(owner, ticket, () => held.promise);
  owner.invalidate();
  held.resolve({ game_id: "game-a", won: true, score: 1000 });
  assert.deepEqual(await result, { kind: "stale" });
  assert.equal(owner.finish(ticket), false);
});

test("an invalidated action cannot finish or adopt over a new same-ID operation", async () => {
  const owner = createContextoActionOwner(pointer());
  const old = owner.begin("game-a");
  const held = deferred();
  const result = recoverOwnedContextoAction(owner, old, () => held.promise);
  owner.invalidate();
  const current = owner.begin("game-a");
  held.resolve({ game_id: "game-a", won: true });
  assert.deepEqual(await result, { kind: "stale" });
  assert.equal(owner.finish(old), false);
  assert.equal(owner.isCurrent(current), true);
  assert.equal(owner.hasPending(), true);
});

test("a different saved game before recovery prevents even the old GET", async () => {
  const active = pointer();
  const owner = createContextoActionOwner(active);
  const ticket = owner.begin("game-a");
  active.set("game-b");
  let reads = 0;
  const result = await recoverOwnedContextoAction(owner, ticket, async () => {
    reads += 1;
    return { game_id: "game-a" };
  });
  assert.deepEqual(result, { kind: "changed" });
  assert.equal(reads, 0);
  assert.equal(active.peek(), "game-b");
});

test("beginning from a displayed old round pauses before work when another ID is already saved", async () => {
  const active = pointer("game-b");
  const owner = createContextoActionOwner(active);
  const ticket = owner.begin("game-a");
  assert.equal(ticket.savedId, "game-b");
  assert.equal(owner.owns(ticket), false);
  let reads = 0;
  assert.deepEqual(await recoverOwnedContextoAction(owner, ticket, async () => {
    reads += 1;
    return { game_id: "game-a", won: true };
  }), { kind: "changed" });
  assert.equal(reads, 0);
  assert.equal(owner.finish(ticket), true);
  assert.equal(active.peek(), "game-b");
});

for (const response of ["success", "missing", "failed"]) {
  test(`a pointer change during a ${response} read suppresses adoption and pointer cleanup`, async () => {
    const active = pointer();
    const owner = createContextoActionOwner(active);
    const ticket = owner.begin("game-a");
    const held = deferred();
    const result = recoverOwnedContextoAction(owner, ticket, () => held.promise,
      (error) => error.status === 404);
    active.set("game-b");
    if (response === "success") held.resolve({ game_id: "game-a", won: true, score: 1000 });
    else held.reject({ status: response === "missing" ? 404 : 503 });
    assert.deepEqual(await result, { kind: "changed" });
    assert.equal(active.peek(), "game-b");
    assert.equal(owner.finish(ticket), true); // Local busy cleanup is still safe.
  });
}

test("a locally owned round can recover when browser storage is unavailable", async () => {
  const active = pointer(null);
  const owner = createContextoActionOwner(active);
  const ticket = owner.begin("game-a");
  assert.equal(owner.owns(ticket), true);
  assert.deepEqual(await recoverOwnedContextoAction(owner, ticket,
    async () => ({ game_id: "game-a", won: false })), {
    kind: "recovered", state: { game_id: "game-a", won: false },
  });
  assert.equal(active.peek(), null);
});

test("a new stored pointer disowns a formerly local-only recovery", async () => {
  const active = pointer(null);
  const owner = createContextoActionOwner(active);
  const ticket = owner.begin("game-a");
  const held = deferred();
  const result = recoverOwnedContextoAction(owner, ticket, () => held.promise);
  active.set("game-b");
  held.resolve({ game_id: "game-a", won: true });
  assert.deepEqual(await result, { kind: "changed" });
});

for (const state of [{ game_id: "other", won: true, score: 1000 }, { won: true }]) {
  test(`a mismatched or missing response ID cannot become the owned state (${state.game_id})`, async () => {
    const owner = createContextoActionOwner(pointer());
    const ticket = owner.begin("game-a");
    assert.deepEqual(await recoverOwnedContextoAction(owner, ticket, async () => state), { kind: "failed" });
  });
}

test("manual recovery can acquire a fresh read after a failed one finishes", async () => {
  const owner = createContextoActionOwner(pointer());
  const failed = owner.begin("game-a");
  let reads = 0;
  assert.deepEqual(await recoverOwnedContextoAction(owner, failed, async () => {
    reads += 1;
    throw new Error("offline");
  }), { kind: "failed" });
  assert.equal(owner.begin("game-a"), null);
  owner.finish(failed);
  const retry = owner.begin("game-a");
  assert.deepEqual(await recoverOwnedContextoAction(owner, retry, async () => {
    reads += 1;
    return { game_id: "game-a", won: true };
  }), { kind: "recovered", state: { game_id: "game-a", won: true } });
  assert.equal(reads, 2);
});
