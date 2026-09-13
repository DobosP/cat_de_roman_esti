import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";
import { createGameActionOwner, recoverOwnedGameAction } from "../src/gameActionRecovery.mjs";

const read = (path) => readFileSync(new URL(path, import.meta.url), "utf8");
const intrusul = read("../src/screens/Intrusul.tsx");
const perechi = read("../src/screens/Perechi.tsx");
const resultCard = read("../src/components/ResultCard.tsx");
const gameShell = read("../src/components/GameShell.tsx");

for (const game of ["intrusul", "perechi"]) {
  test(`${game} retry preserves the exact public earned snapshot after read failure`, async () => {
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

test("create and replay are single-flight with visible result busy state", () => {
  for (const screen of [intrusul, perechi]) {
    assert.match(screen, /const startInFlight = useRef\(false\)/);
    assert.match(screen, /if \(!acquireFlight\(startInFlight\)\) return/);
    assert.match(screen, /releaseFlight\(startInFlight\)/);
    assert.match(screen, /actionsBusy=\{loading\}/);
    assert.equal((screen.match(/busy=\{loading\}/g) ?? []).length, 2);
    assert.match(screen, /const exitSafely = useCallback/);
  }
  assert.match(resultCard, /actionsBusy = false/);
  assert.match(resultCard, /disabled=\{actionsBusy\}/);
  assert.match(resultCard, /actionsBusy \? "Se pregătește…" : replayLabel/);
  assert.match(gameShell, /busy = false/);
  assert.match(gameShell, /disabled=\{busy\}/);
  assert.match(gameShell, /aria-busy=\{busy \|\| undefined\}/);
  assert.match(gameShell, /busy \? "Se pregătește…" : "Ieși"/);
});

test("quick games explain locked hints and visibly price only the available hint action", () => {
  assert.match(intrusul, /<span className="intrusul-hint-status">Indiciu disponibil după prima greșeală\.<\/span>/);
  assert.match(perechi, /<span className="perechi-hint-status">Indiciu disponibil după două greșeli\.<\/span>/);
  for (const screen of [intrusul, perechi]) {
    assert.match(screen, /!finished && !state\.hints_used && \([\s\S]*?state\.hint_available \? \(\s*<Button/);
    assert.match(screen, /onClick=\{\(\) => void requestHint\(\)\}/);
    assert.match(screen, /Costă 150 de puncte\./);
    assert.match(screen, /💡 Arată (?:indiciul|o pereche) · −150 pct/);
  }
});
