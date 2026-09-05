import assert from "node:assert/strict";
import test from "node:test";
import {
  createSavedGameResume,
  subscribeSavedGameResume,
} from "../src/savedGameResume.mjs";

const terminal = (state) => state.finished;
const isMissing = (error) => error?.status === 404;

function savedPointer(id) {
  return {
    id,
    forgets: 0,
    peek() {
      return this.id;
    },
    forget() {
      this.forgets += 1;
      this.id = null;
    },
  };
}

function attempt({
  id = "game-1",
  load,
  terminalPolicy = "discard",
  transient = "forget",
}) {
  const active = savedPointer(id);
  return {
    active,
    resume: createSavedGameResume({
      active,
      load,
      isTerminal: terminal,
      terminal: terminalPolicy,
      transient,
      isMissing,
    }),
  };
}

function subscribe(resume, events, { reportFailures = true } = {}) {
  const handlers = {
    setPending: (pending) => events.push(["pending", pending]),
    onResume: (state, detail) => events.push(["resumed", state, detail]),
  };
  if (reportFailures) {
    handlers.onTransientError = (error) => events.push(["failed", error]);
  }
  return subscribeSavedGameResume(resume, handlers);
}

test("no saved id completes without loading or forgetting", async () => {
  let loads = 0;
  const { active, resume } = attempt({
    id: null,
    load: async () => {
      loads += 1;
      return { finished: false };
    },
  });
  const events = [];

  subscribe(resume, events);
  assert.deepEqual(await resume.runOnce(), { kind: "none" });
  await Promise.resolve();

  assert.equal(loads, 0);
  assert.equal(active.forgets, 0);
  assert.deepEqual(events, [["pending", false]]);
});

test("a live saved game loads once, stays remembered, and is delivered", async () => {
  let loads = 0;
  const state = { finished: false, difficulty: "greu", board_category: "istorie" };
  const { active, resume } = attempt({
    load: async (id) => {
      loads += 1;
      assert.equal(id, "game-1");
      return state;
    },
  });
  const events = [];

  subscribe(resume, events);
  await resume.runOnce();
  await Promise.resolve();

  assert.equal(loads, 1);
  assert.equal(active.id, "game-1");
  assert.deepEqual(events, [
    ["pending", true],
    ["resumed", state, { gameId: "game-1", terminal: false }],
    ["pending", false],
  ]);
});

test("terminal policy preserves legacy discard and derived-game adoption", async () => {
  const state = { finished: true, score: 88 };
  const discarded = attempt({ load: async () => state });
  const discardEvents = [];
  subscribe(discarded.resume, discardEvents);
  assert.equal((await discarded.resume.runOnce()).kind, "terminal-discarded");
  await Promise.resolve();

  assert.equal(discarded.active.id, null);
  assert.deepEqual(discardEvents, [
    ["pending", true],
    ["pending", false],
  ]);

  const adopted = attempt({
    load: async () => state,
    terminalPolicy: "adopt",
  });
  const adoptEvents = [];
  subscribe(adopted.resume, adoptEvents);
  await adopted.resume.runOnce();
  await Promise.resolve();

  assert.equal(adopted.active.id, "game-1");
  assert.deepEqual(adoptEvents, [
    ["pending", true],
    ["resumed", state, { gameId: "game-1", terminal: true }],
    ["pending", false],
  ]);
});

test("404 forgets the stale id without surfacing a transient failure", async () => {
  const missing = Object.assign(new Error("expired"), { status: 404 });
  const { active, resume } = attempt({
    load: async () => {
      throw missing;
    },
    transient: "retain",
  });
  const events = [];

  subscribe(resume, events);
  assert.equal((await resume.runOnce()).kind, "missing");
  await Promise.resolve();

  assert.equal(active.id, null);
  assert.equal(active.forgets, 1);
  assert.deepEqual(events, [
    ["pending", true],
    ["pending", false],
  ]);
});

test("transient policy either forgets silently or retains and reports", async () => {
  const offline = new Error("offline");
  for (const transient of ["forget", "retain"]) {
    const { active, resume } = attempt({
      load: async () => {
        throw offline;
      },
      transient,
    });
    const events = [];

    subscribe(resume, events, { reportFailures: transient === "retain" });
    assert.equal((await resume.runOnce()).kind, "failed");
    await Promise.resolve();

    assert.equal(active.id, transient === "forget" ? null : "game-1");
    assert.deepEqual(
      events,
      transient === "forget"
        ? [
            ["pending", true],
            ["pending", false],
          ]
        : [
            ["pending", true],
            ["failed", offline],
            ["pending", false],
          ],
    );
  }
});

test("StrictMode-style resubscribe shares one request and suppresses stale delivery", async () => {
  let resolveLoad;
  let loads = 0;
  const loaded = new Promise((resolve) => {
    resolveLoad = resolve;
  });
  const { resume } = attempt({
    load: async () => {
      loads += 1;
      return loaded;
    },
  });
  const firstEvents = [];
  const secondEvents = [];

  const unsubscribeFirst = subscribe(resume, firstEvents);
  unsubscribeFirst();
  subscribe(resume, secondEvents);
  resolveLoad({ finished: false });
  await resume.runOnce();
  await Promise.resolve();

  assert.equal(loads, 1);
  assert.deepEqual(firstEvents, [["pending", true]]);
  assert.deepEqual(secondEvents, [
    ["pending", true],
    ["resumed", { finished: false }, { gameId: "game-1", terminal: false }],
    ["pending", false],
  ]);
});

test("unmount suppresses late state, feedback, and pending delivery", async () => {
  let resolveLoad;
  const loaded = new Promise((resolve) => {
    resolveLoad = resolve;
  });
  const { resume } = attempt({ load: async () => loaded });
  const events = [];

  const unsubscribe = subscribe(resume, events);
  unsubscribe();
  resolveLoad({ finished: false });
  await resume.runOnce();
  await Promise.resolve();

  assert.deepEqual(events, [["pending", true]]);
});
