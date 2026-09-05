import assert from "node:assert/strict";
import test from "node:test";
import { createSavedGameResume, subscribeSavedGameResume } from "../src/savedGameResume.mjs";

const terminal = (state) => state.finished;
const isMissing = (error) => error?.status === 404;
function savedPointer(id = "game-1") {
  return {
    id, conditionalForgets: [],
    peek() { return this.id; },
    isCurrent(gameId) { return this.id === gameId; },
    forgetIfCurrent(gameId) {
      this.conditionalForgets.push(gameId);
      if (!this.isCurrent(gameId)) return false;
      this.id = null;
      return true;
    },
  };
}
function attempt({ id = "game-1", active = savedPointer(id), load }) {
  return { active, resume: createSavedGameResume({ active, load, isTerminal: terminal, isMissing }) };
}
function subscribe(resume, events) {
  return subscribeSavedGameResume(resume, {
    setPending: (pending) => events.push(["pending", pending]),
    onResume: (state, detail) => events.push(["resumed", state, detail]),
    onTransientError: (error) => events.push(["failed", error]),
    onSuperseded: (hasCurrent) => events.push(["changed", hasCurrent]),
  });
}

test("no saved id completes without loading or clearing storage", async () => {
  let loads = 0;
  const { active, resume } = attempt({ id: null, load: async () => { loads += 1; } });
  const events = [];
  subscribe(resume, events);
  assert.deepEqual(await resume.runOnce(), { kind: "none" });
  await Promise.resolve();
  assert.equal(loads, 0);
  assert.deepEqual(active.conditionalForgets, []);
  assert.deepEqual(events, [["pending", false]]);
});

test("live and terminal saved games are adopted and remain remembered", async () => {
  for (const finished of [false, true]) {
    let loads = 0;
    const state = { finished, difficulty: "greu", board_category: "istorie" };
    const { active, resume } = attempt({ load: async (id) => { loads += 1; assert.equal(id, "game-1"); return state; } });
    const events = [];
    subscribe(resume, events);
    await resume.runOnce(); await Promise.resolve();
    assert.equal(loads, 1);
    assert.equal(active.id, "game-1");
    assert.deepEqual(events, [["pending", true], ["resumed", state, { gameId: "game-1", terminal: finished }], ["pending", false]]);
  }
});

test("404 conditionally clears its ID while a transient failure retains it", async () => {
  const missing = Object.assign(new Error("expired"), { status: 404 });
  const expired = attempt({ load: async () => { throw missing; } });
  const expiredEvents = [];
  subscribe(expired.resume, expiredEvents);
  assert.equal((await expired.resume.runOnce()).kind, "missing"); await Promise.resolve();
  assert.equal(expired.active.id, null);
  assert.deepEqual(expired.active.conditionalForgets, ["game-1"]);
  assert.deepEqual(expiredEvents, [["pending", true], ["pending", false]]);

  const offline = new Error("offline");
  const transient = attempt({ load: async () => { throw offline; } });
  const transientEvents = [];
  subscribe(transient.resume, transientEvents);
  assert.equal((await transient.resume.runOnce()).kind, "failed"); await Promise.resolve();
  assert.equal(transient.active.id, "game-1");
  assert.deepEqual(transientEvents, [["pending", true], ["failed", offline], ["pending", false]]);
});

test("late success, 404, and transient outcomes cannot overwrite a newer pointer", async () => {
  for (const result of ["success", "missing", "failed"]) {
    let settle;
    const response = new Promise((resolve, reject) => { settle = result === "success" ? resolve : reject; });
    const { active, resume } = attempt({ load: async () => response });
    const events = [];
    subscribe(resume, events);
    active.id = "game-2";
    settle(result === "success" ? { finished: false } : Object.assign(new Error(result), { status: result === "missing" ? 404 : 503 }));
    assert.equal((await resume.runOnce()).kind, "superseded"); await Promise.resolve();
    assert.equal(active.id, "game-2");
    assert.deepEqual(active.conditionalForgets, []);
    assert.deepEqual(events, [["pending", true], ["changed", true], ["pending", false]]);
  }
});

test("a settled outcome is rechecked before delivery", async () => {
  const { active, resume } = attempt({ load: async () => ({ finished: false }) });
  assert.equal((await resume.runOnce()).kind, "resumed");
  active.id = "game-2";
  const events = [];
  subscribe(resume, events); await Promise.resolve();
  assert.deepEqual(events, [["pending", true], ["changed", true], ["pending", false]]);
});

test("StrictMode resubscribe shares one request and unmount suppresses delivery", async () => {
  let resolveLoad; let loads = 0;
  const loaded = new Promise((resolve) => { resolveLoad = resolve; });
  const { resume } = attempt({ load: async () => { loads += 1; return loaded; } });
  const first = []; const second = [];
  const unsubscribe = subscribe(resume, first); unsubscribe(); subscribe(resume, second);
  resolveLoad({ finished: false }); await resume.runOnce(); await Promise.resolve();
  assert.equal(loads, 1);
  assert.deepEqual(first, [["pending", true]]);
  assert.deepEqual(second, [["pending", true], ["resumed", { finished: false }, { gameId: "game-1", terminal: false }], ["pending", false]]);
});

test("cancel before create prevents an old resume from clearing the new loading owner", async () => {
  let resolveLoad;
  const loaded = new Promise((resolve) => { resolveLoad = resolve; });
  const { resume } = attempt({ load: async () => loaded });
  const events = [];
  const cancelResume = subscribe(resume, events);
  cancelResume();
  events.push(["create-pending", true]);
  resolveLoad({ finished: false });
  await resume.runOnce(); await Promise.resolve();
  assert.deepEqual(events, [["pending", true], ["create-pending", true]]);
});

test("unmounted terminal/transient retain their ID; unmounted 404 clears only its ID", async () => {
  for (const result of ["terminal", "failed", "missing", "replaced-missing"]) {
    let settle;
    const loaded = new Promise((resolve, reject) => { settle = result === "terminal" ? resolve : reject; });
    const { active, resume } = attempt({ load: async () => loaded });
    const events = []; const unsubscribe = subscribe(resume, events); unsubscribe();
    if (result === "replaced-missing") active.id = "game-2";
    settle(result === "terminal" ? { finished: true } : Object.assign(new Error(result), { status: result.includes("missing") ? 404 : 503 }));
    await resume.runOnce();
    assert.equal(active.id, result === "missing" ? null : result === "replaced-missing" ? "game-2" : "game-1");
    assert.deepEqual(events, [["pending", true]]);
  }
});

test("a retry attempt snapshots the latest pointer and loads it once", async () => {
  const active = savedPointer(); const loads = [];
  const load = async (id) => { loads.push(id); if (id === "game-1") throw new Error("offline"); return { finished: false }; };
  assert.equal((await attempt({ active, load }).resume.runOnce()).kind, "failed");
  active.id = "game-2";
  assert.equal((await attempt({ active, load }).resume.runOnce()).kind, "resumed");
  assert.deepEqual(loads, ["game-1", "game-2"]);
});
