import assert from "node:assert/strict";
import test from "node:test";
import { createGameActionOwner, recoverOwnedGameAction } from "../src/gameActionRecovery.mjs";

for (const game of ["intrusul", "perechi"]) {
  void test(`${game} retry preserves the exact public earned snapshot after read failure`, async () => {
    const owner = createGameActionOwner({ peek: () => "owned", isCurrent: (id) => id === "owned" });
    const snapshot = game === "intrusul"
      ? { game_id: "owned", wrong_ids: ["one"], attempts: 1, mistakes: 1, hints_used: 1, clue: { label: "group", message: "earned clue" }, won: false, lost: false }
      : { game_id: "owned", solved_pairs: [{ tiles: [{ id: "one" }, { id: "two" }], label: "earned pair" }], solved_count: 1, hints_used: 1, hint: { label: "earned hint" }, won: false, lost: false };
    const ticket = owner.begin("owned");
    assert.equal((await recoverOwnedGameAction(owner, ticket, async () => { throw Error("offline"); })).kind, "failed");
    owner.finish(ticket);
    const retry = owner.begin("owned");
    const outcome = await recoverOwnedGameAction(owner, retry, async () => snapshot);
    assert.equal(outcome.kind, "recovered");
    assert.strictEqual(outcome.state, snapshot);
    assert.equal(outcome.state.solution, undefined);
    assert.equal(outcome.state.score, undefined);
    owner.finish(retry);
  });
}
