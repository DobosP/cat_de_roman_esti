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
  for (const raw of ["{broken", "null", "x".repeat(65537), JSON.stringify({ version: 1, ...state({ progress: { world_id: "kitchen-v1", recipe_hash: HASH, discoveries: Array(257).fill(["a", "b"]) } }) })]) {
    const store = storage();
    store.setItem(key, raw);
    assert.equal(read(store).kind, "invalid");
    assert.equal((await save(state(), raw, store, null)).kind, "changed");
    assert.equal(store.getItem(key), raw);
  }
});

test("large earned collections remain readable through the 256-craft checkpoint boundary", async () => {
  const store = storage();
  let expected = null;
  for (const count of [129, 200, 256]) {
    const progress = { ...state().progress, discoveries: Array.from({ length: count }, (_, i) => [`ingredient-${i}`, "water"]) };
    const result = await save(state({ revision: count, progress }), expected, store, null);
    assert.equal(result.kind, "saved");
    assert.ok(Buffer.byteLength(result.raw, "utf8") < 64 * 1024);
    assert.equal(read(store).kind, "saved");
    assert.deepEqual(read(store).value.progress, progress);
    expected = result.raw;
  }
  const excessive = { ...state().progress, discoveries: Array.from({ length: 257 }, (_, i) => [`ingredient-${i}`, "water"]) };
  assert.equal((await save(state({ revision: 257, progress: excessive }), expected, store, null)).kind, "unavailable");
  assert.equal(store.getItem(key), expected);
});

test("the 64 KiB checkpoint limit counts UTF-8 bytes and preserves a smaller valid save", async () => {
  const store = storage();
  const original = await save(state(), null, store, null);
  const oversized = state({ progress: {
    ...state().progress,
    discoveries: Array.from({ length: 128 }, (_, i) => [`${i}${"ș".repeat(240)}`, `b${"ț".repeat(240)}`]),
  } });
  const raw = JSON.stringify({ version: 1, ...oversized });
  assert.ok(raw.length < 64 * 1024);
  assert.ok(Buffer.byteLength(raw, "utf8") > 64 * 1024);
  assert.equal((await save(oversized, original.raw, store, null)).kind, "unavailable");
  assert.equal(store.getItem(key), original.raw);
  store.setItem(key, raw);
  assert.equal(read(store).kind, "invalid");
  assert.equal((await save(state(), raw, store, null)).kind, "changed");
  assert.equal(store.getItem(key), raw);
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

test("late discoveries from both earlier worlds merge into a larger third-version collection", async () => {
  const store = storage();
  const middleHash = "b".repeat(64);
  const newestHash = "c".repeat(64);
  const original = await save(state(), null, store, null);
  const middle = state({ game_id: "111-world-session", compatible_recipe_hashes: [HASH], progress: {
    ...state().progress, recipe_hash: middleHash,
    discoveries: [["flour", "water"], ["dough", "heat"]],
  } });
  const upgraded = await save(middle, original.raw, store, null);
  const newest = state({ game_id: "large-world-session", compatible_recipe_hashes: [HASH, middleHash], progress: {
    ...middle.progress, recipe_hash: newestHash,
    discoveries: [...middle.progress.discoveries, ...Array.from({ length: 128 }, (_, i) => [`ingredient-${i}`, "water"])],
  } });
  await save(newest, upgraded.raw, store, null);
  const lateOriginal = state({ revision: 9, progress: {
    ...state().progress, discoveries: [["flour", "water"], ["flour", "egg"]],
  } });
  assert.equal((await save(lateOriginal, original.raw, store, null)).kind, "merged");
  const lateMiddle = { ...middle, revision: 12, progress: {
    ...middle.progress, discoveries: [...middle.progress.discoveries, ["bread", "jam"]],
  } };
  assert.equal((await save(lateMiddle, upgraded.raw, store, null)).kind, "merged");
  const current = read(store);
  assert.equal(current.kind, "saved");
  assert.equal(current.value.game_id, newest.game_id);
  assert.equal(current.value.progress.recipe_hash, newestHash);
  assert.equal(current.value.progress.discoveries.length, 132);
  assert.deepEqual(current.value.progress.discoveries.slice(-2), [["flour", "egg"], ["bread", "jam"]]);
  assert.deepEqual(current.value.compatible_recipe_hashes, [HASH, middleHash]);
  assert.equal(current.value.needs_restore, true);
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
  assert.equal(merge({ world_id: "a", recipe_hash: HASH, discoveries: Array.from({ length: 256 }, (_, i) => [`a${i}`, "b"]) }, { world_id: "a", recipe_hash: HASH, discoveries: [["extra", "b"]] }), null);
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
  for (const compatible_recipe_hashes of [null, {}, ["x"], [HASH], ["b".repeat(64), "b".repeat(64)], Array.from({ length: 17 }, (_, i) => i.toString(16).padStart(64, "0"))]) {
    store.setItem(key, JSON.stringify({ ...legacy, compatible_recipe_hashes }));
    assert.equal(read(store).kind, "invalid");
  }
});

test("nine through sixteen compatible books remain usable after the first owned save", async () => {
  for (const count of [9, 16]) {
    const store = storage();
    const compatible_recipe_hashes = Array.from({ length: count }, (_, i) => i.toString(16).padStart(64, "0"));
    const initial = state({ revision: 0, compatible_recipe_hashes, progress: { ...state().progress, discoveries: [] } });
    const created = await save(initial, null, store, null);
    assert.equal(created.kind, "saved");
    assert.equal(read(store).kind, "saved");
    const advanced = state({ compatible_recipe_hashes });
    const updated = await save(advanced, created.raw, store, null);
    assert.equal(updated.kind, "saved");
    const restored = read(store);
    assert.equal(restored.kind, "saved");
    assert.equal(restored.value.game_id, initial.game_id);
    assert.equal(restored.value.revision, advanced.revision);
    assert.deepEqual(restored.value.progress, advanced.progress);
    assert.deepEqual(restored.value.compatible_recipe_hashes, compatible_recipe_hashes);
  }
});

test("the bundled world's compatibility metadata survives an owned update and reload", async () => {
  const catalog = JSON.parse(readFileSync(new URL("../../cat_de_roman_esti/fixtures/alchimie_discovery_world_v92.json", import.meta.url), "utf8"));
  const compatible_recipe_hashes = catalog.compatible_versions.map((version) => version.recipe_hash);
  const store = storage();
  const initial = state({ revision: 0, compatible_recipe_hashes, progress: { ...state().progress, discoveries: [] } });
  const created = await save(initial, null, store, null);
  assert.equal(created.kind, "saved");
  assert.equal(read(store).kind, "saved");
  const advanced = state({ compatible_recipe_hashes });
  const updated = await save(advanced, created.raw, store, null);
  assert.equal(updated.kind, "saved");
  const restored = read(store);
  assert.equal(restored.kind, "saved");
  assert.equal(restored.value.revision, advanced.revision);
  assert.deepEqual(restored.value.progress, advanced.progress);
  assert.deepEqual(restored.value.compatible_recipe_hashes, compatible_recipe_hashes);
  assert.equal(restored.value.compatible_versions, undefined);
  assert.equal(restored.value.recipes, undefined);
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
