import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";
import ts from "typescript";

const source = readFileSync(new URL("../src/explorationSave.ts", import.meta.url), "utf8");
const compiled = ts.transpileModule(source, {
  compilerOptions: { module: ts.ModuleKind.ESNext, target: ts.ScriptTarget.ES2021 },
}).outputText;
const { EXPLORATION_SAVE_KEY: key, readExplorationSave: read, saveExplorationState: save, mergeExplorationProgress: merge } =
  await import(`data:text/javascript;base64,${Buffer.from(compiled).toString("base64")}`);
const storage = () => {
  let raw = null;
  return { getItem: () => raw, setItem: (_key, value) => { raw = value; } };
};
const HASH = "a".repeat(64);
const state = (overrides = {}) => ({
  game_id: "world-session", revision: 1, goal_id: null,
  compatible_recipe_hashes: [],
  progress: { world_id: "kitchen-v1", recipe_hash: HASH, discoveries: [["flour", "water"]] }, ...overrides,
});

test("collection stores replay instructions and resumes without private recipe-book data", async () => {
  const store = storage();
  const result = await save(state({ private_book: "never persisted" }), null, store, null);
  assert.equal(result.kind, "saved");
  const value = read(store);
  assert.equal(value.kind, "saved");
  assert.deepEqual(value.value.progress.discoveries, [["flour", "water"]]);
  assert.equal(value.value.private_book, undefined);
});

test("malformed and excessive checkpoints are preserved and never overwritten", async () => {
  for (const raw of ["{broken", "null", "x".repeat(65537), JSON.stringify({ version: 1, ...state({ progress: { world_id: "kitchen-v1", recipe_hash: HASH, discoveries: Array(129).fill(["a", "b"]) } }) })]) {
    const store = storage();
    store.setItem(key, raw);
    assert.equal(read(store).kind, "invalid");
    assert.equal((await save(state(), raw, store, null)).kind, "changed");
    assert.equal(store.getItem(key), raw);
  }
});

test("an older revision cannot replace a more advanced tab", async () => {
  const store = storage();
  const current = await save(state({ revision: 5, goal_id: "bread" }), null, store, null);
  assert.equal((await save(state({ revision: 2 }), current.raw, store, null)).kind, "changed");
  assert.equal(read(store).value.goal_id, "bread");
  assert.equal(read(store).value.revision, 5);
});

test("a server-restored collection replaces its exact old-book checkpoint with the current binding", async () => {
  const store = storage();
  const original = await save(state({ revision: 5, goal_id: "bread" }), null, store, null);
  const restored = state({
    game_id: "migrated-session", revision: 0, goal_id: "bread",
    compatible_recipe_hashes: [HASH],
    progress: { ...state().progress, recipe_hash: "b".repeat(64) },
  });
  assert.equal((await save(restored, original.raw, store, null)).kind, "saved");
  const current = read(store).value;
  assert.deepEqual(current.progress, restored.progress);
  assert.equal(current.goal_id, "bread");
  assert.equal(current.game_id, "migrated-session");
  assert.deepEqual(current.compatible_recipe_hashes, [HASH]);
});

test("a late old-version discovery joins a compatible migrated checkpoint without downgrading it", async () => {
  const store = storage();
  const original = await save(state(), null, store, null);
  const restored = state({
    game_id: "migrated-session", revision: 0,
    compatible_recipe_hashes: [HASH],
    progress: { ...state().progress, recipe_hash: "b".repeat(64) },
  });
  await save(restored, original.raw, store, null);
  const late = state({ revision: 9, progress: {
    ...state().progress, discoveries: [["flour", "water"], ["dough", "heat"]],
  } });
  assert.equal((await save(late, original.raw, store, null)).kind, "merged");
  const current = read(store).value;
  assert.equal(current.game_id, restored.game_id);
  assert.equal(current.progress.recipe_hash, restored.progress.recipe_hash);
  assert.deepEqual(current.progress.discoveries, late.progress.discoveries);
  assert.deepEqual(current.compatible_recipe_hashes, [HASH]);
  assert.equal(current.needs_restore, true);
});

test("a newer response upgrades a concurrent old-book union and keeps compatibility for later replies", async () => {
  const store = storage();
  const original = await save(state(), null, store, null);
  await save(state({ revision: 2, goal_id: "bread", progress: {
    ...state().progress, discoveries: [["flour", "water"], ["flour", "egg"]],
  } }), original.raw, store, null);
  const restored = state({
    game_id: "migrated-session", revision: 0, compatible_recipe_hashes: [HASH],
    progress: { ...state().progress, recipe_hash: "b".repeat(64), discoveries: [["flour", "water"], ["dough", "heat"]] },
  });
  assert.equal((await save(restored, original.raw, store, null)).kind, "merged");
  const current = read(store).value;
  assert.equal(current.game_id, restored.game_id);
  assert.equal(current.goal_id, "bread");
  assert.equal(current.progress.recipe_hash, restored.progress.recipe_hash);
  assert.deepEqual(current.progress.discoveries, [["flour", "water"], ["flour", "egg"], ["dough", "heat"]]);
  assert.deepEqual(current.compatible_recipe_hashes, [HASH]);
  assert.equal(current.needs_restore, true);
});

test("an unrelated recipe book cannot overwrite or merge with a migrated checkpoint", async () => {
  const store = storage();
  const original = await save(state(), null, store, null);
  const restored = state({
    game_id: "migrated-session", compatible_recipe_hashes: [HASH],
    progress: { ...state().progress, recipe_hash: "b".repeat(64) },
  });
  const migrated = await save(restored, original.raw, store, null);
  const unrelated = state({ progress: {
    ...state().progress, recipe_hash: "c".repeat(64), discoveries: [["egg", "milk"]],
  } });
  assert.equal((await save(unrelated, original.raw, store, null)).kind, "changed");
  assert.equal(store.getItem(key), migrated.raw);
});

test("concurrent discoveries in separate sessions form a replayable union", async () => {
  const store = storage();
  const original = await save(state(), null, store, null);
  await save(state({ game_id: "second", progress: { world_id: "kitchen-v1", recipe_hash: HASH, discoveries: [["flour", "water"], ["dough", "heat"]] } }), original.raw, store, null);
  const result = await save(state({ revision: 2, progress: { world_id: "kitchen-v1", recipe_hash: HASH, discoveries: [["flour", "water"], ["flour", "egg"]] } }), original.raw, store, null);
  assert.equal(result.kind, "merged");
  const merged = read(store).value;
  assert.equal(merged.needs_restore, true);
  assert.equal(merged.game_id, "second");
  assert.deepEqual(merged.progress.discoveries, [["flour", "water"], ["dough", "heat"], ["flour", "egg"]]);
  await save(state({ game_id: "restored", revision: 0, progress: merged.progress }), result.raw, store, null);
  assert.equal(read(store).value.needs_restore, undefined);
  assert.equal(read(store).value.game_id, "restored");
});

test("union keeps ingredient order, drops duplicate pairs, and respects world and size bounds", () => {
  assert.deepEqual(merge({ world_id: "a", recipe_hash: HASH, discoveries: [["a", "b"]] }, { world_id: "a", recipe_hash: HASH, discoveries: [["b", "a"], ["c", "d"]] }).discoveries, [["a", "b"], ["c", "d"]]);
  assert.equal(merge({ world_id: "a", recipe_hash: HASH, discoveries: [] }, { world_id: "b", recipe_hash: HASH, discoveries: [] }), null);
  assert.equal(merge({ world_id: "a", recipe_hash: HASH, discoveries: [] }, { world_id: "a", recipe_hash: "b".repeat(64), discoveries: [] }), null);
  assert.equal(merge({ world_id: "a", recipe_hash: HASH, discoveries: Array.from({ length: 128 }, (_, i) => [`a${i}`, "b"]) }, { world_id: "a", recipe_hash: HASH, discoveries: [["extra", "b"]] }), null);
});

test("a checkpoint requires the exact lowercase recipe-book binding", () => {
  for (const recipe_hash of [undefined, "a".repeat(63), "A".repeat(64), "z".repeat(64)]) {
    const store = storage();
    store.setItem(key, JSON.stringify({ version: 1, ...state({ progress: { world_id: "kitchen-v1", recipe_hash, discoveries: [] } }) }));
    assert.equal(read(store).kind, "invalid");
  }
});

test("legacy saves remain readable while compatibility metadata stays bounded and well formed", () => {
  const store = storage();
  const legacy = { version: 1, ...state() };
  delete legacy.compatible_recipe_hashes;
  store.setItem(key, JSON.stringify(legacy));
  assert.equal(read(store).kind, "saved");
  for (const compatible_recipe_hashes of [null, {}, ["x"], [HASH], ["b".repeat(64), "b".repeat(64)], Array.from({ length: 9 }, (_, i) => String(i).repeat(64))]) {
    store.setItem(key, JSON.stringify({ ...legacy, compatible_recipe_hashes }));
    assert.equal(read(store).kind, "invalid");
  }
});

test("unavailable storage reports explicitly without crashing play", async () => {
  const broken = { getItem() { throw new Error("blocked"); }, setItem() { throw new Error("blocked"); } };
  assert.equal(read(broken).kind, "unavailable");
  assert.equal((await save(state(), null, broken, null)).kind, "unavailable");
  assert.equal((await save(state(), null, null, null)).kind, "unavailable");
});

test("browser locks serialize competing saves and preserve both discoveries", async () => {
  const store = storage();
  let tail = Promise.resolve();
  const locks = { request(_name, callback) { const result = tail.then(callback); tail = result; return result; } };
  await Promise.all([
    save(state(), null, store, locks),
    save(state({ game_id: "second", progress: { world_id: "kitchen-v1", recipe_hash: HASH, discoveries: [["egg", "milk"]] } }), null, store, locks),
  ]);
  assert.equal(read(store).value.progress.discoveries.length, 2);
  assert.equal(read(store).value.needs_restore, true);
});

test("a screen leaving while its storage lock waits cannot write afterward", async () => {
  const store = storage();
  const result = await save(state(), null, store, { request: (_name, callback) => callback() }, () => false);
  assert.equal(result.kind, "changed");
  assert.equal(read(store).kind, "empty");
});
