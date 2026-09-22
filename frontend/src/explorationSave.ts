import type { ExplorationProgress, ExplorationState } from "./api/alchimieExplore";

export const EXPLORATION_SAVE_KEY = "cat_alchimie_exploration_v1";
const MAX_SAVE_BYTES = 64 * 1024;
const MAX_DISCOVERIES = 256;
// Match the bounded server history in wordgames/discovery_world.py.
const MAX_COMPATIBLE_VERSIONS = 16;
const encoder = new TextEncoder();
type SaveStorage = Pick<Storage, "getItem" | "setItem">;

export interface ExplorationSave {
  version: 1;
  game_id: string;
  revision: number;
  progress: ExplorationProgress;
  goal_id: string | null;
  /** Older books whose recipes the server guarantees this version preserves. */
  compatible_recipe_hashes?: string[];
  /** A cross-tab union must be replayed before its saved session is used. */
  needs_restore?: boolean;
}

export type SaveRead =
  | { kind: "saved"; value: ExplorationSave; raw: string }
  | { kind: "empty" | "unavailable"; raw: null }
  | { kind: "invalid"; raw: string };

function browserStorage(): SaveStorage | null {
  try { return localStorage; } catch { return null; }
}

function validId(value: unknown): value is string {
  return typeof value === "string" && value.length > 0 && value.length <= 256;
}

function exceedsSaveLimit(raw: string): boolean {
  return raw.length > MAX_SAVE_BYTES || encoder.encode(raw).byteLength > MAX_SAVE_BYTES;
}

export function readExplorationSave(storage: SaveStorage | null = browserStorage()): SaveRead {
  if (!storage) return { kind: "unavailable", raw: null };
  let raw: string | null;
  try { raw = storage.getItem(EXPLORATION_SAVE_KEY); } catch { return { kind: "unavailable", raw: null }; }
  if (raw === null) return { kind: "empty", raw: null };
  if (exceedsSaveLimit(raw)) return { kind: "invalid", raw };
  try {
    const value = JSON.parse(raw) as ExplorationSave;
    if (value?.version !== 1 || !validId(value.game_id) ||
      !Number.isSafeInteger(value.revision) || value.revision < 0 ||
      (value.goal_id !== null && !validId(value.goal_id)) ||
      (value.needs_restore !== undefined && typeof value.needs_restore !== "boolean") ||
      !validId(value.progress?.world_id) || !/^[a-f0-9]{64}$/.test(value.progress.recipe_hash) ||
      (value.compatible_recipe_hashes !== undefined && (
        !Array.isArray(value.compatible_recipe_hashes) || value.compatible_recipe_hashes.length > MAX_COMPATIBLE_VERSIONS ||
        new Set(value.compatible_recipe_hashes).size !== value.compatible_recipe_hashes.length ||
        value.compatible_recipe_hashes.some((hash) => typeof hash !== "string" || !/^[a-f0-9]{64}$/.test(hash) || hash === value.progress.recipe_hash)
      )) ||
      !Array.isArray(value.progress.discoveries) ||
      value.progress.discoveries.length > MAX_DISCOVERIES || value.progress.discoveries.some((pair) =>
        !Array.isArray(pair) || pair.length !== 2 || !pair.every(validId) || pair[0] === pair[1])) {
      return { kind: "invalid", raw };
    }
    return { kind: "saved", value, raw };
  } catch { return { kind: "invalid", raw }; }
}

type SaveResult = { kind: "saved" | "merged"; raw: string } | { kind: "changed" | "unavailable" };

/** Preserve both valid recipe sequences if separate live sessions advanced at once. */
export function mergeExplorationProgress(
  a: ExplorationProgress, b: ExplorationProgress,
  aCompatible: string[] = [], bCompatible: string[] = [],
): ExplorationProgress | null {
  if (a.world_id !== b.world_id) return null;
  let recipeHash = a.recipe_hash;
  if (a.recipe_hash !== b.recipe_hash) {
    const aPreservesB = aCompatible.includes(b.recipe_hash);
    const bPreservesA = bCompatible.includes(a.recipe_hash);
    // Only an explicit, unambiguous server compatibility declaration can upgrade a union.
    if (aPreservesB === bPreservesA) return null;
    recipeHash = aPreservesB ? a.recipe_hash : b.recipe_hash;
  }
  const pairs = new Set<string>();
  const discoveries: [string, string][] = [];
  for (const pair of [...a.discoveries, ...b.discoveries]) {
    const key = JSON.stringify([...pair].sort());
    if (pairs.has(key)) continue;
    pairs.add(key);
    discoveries.push(pair);
  }
  return discoveries.length <= MAX_DISCOVERIES ? { world_id: a.world_id, recipe_hash: recipeHash, discoveries } : null;
}

/** A browser lock serializes compare-and-write across tabs when supported. */
export async function saveExplorationState(
  state: ExplorationState,
  expectedRaw: string | null,
  storage: SaveStorage | null = browserStorage(),
  locks: Pick<LockManager, "request"> | null = typeof navigator === "undefined" ? null : navigator.locks ?? null,
  maySave: () => boolean = () => true,
): Promise<SaveResult> {
  const transaction = (): SaveResult => {
    if (!maySave()) return { kind: "changed" };
    if (!storage) return { kind: "unavailable" };
    const current = readExplorationSave(storage);
    if (current.kind === "unavailable") return { kind: "unavailable" };
    if (current.kind === "invalid") return { kind: "changed" };
    let value: ExplorationSave = {
      version: 1, game_id: state.game_id, revision: state.revision,
      progress: state.progress, goal_id: state.goal_id,
      compatible_recipe_hashes: state.compatible_recipe_hashes ?? [],
    };
    let kind: "saved" | "merged" = "saved";
    if (current.raw !== expectedRaw || (current.kind === "saved" && current.value.game_id === state.game_id && current.value.revision > state.revision)) {
      if (current.kind !== "saved") return { kind: "changed" };
      const progress = mergeExplorationProgress(
        current.value.progress, state.progress,
        current.value.compatible_recipe_hashes, state.compatible_recipe_hashes,
      );
      if (!progress) return { kind: "changed" };
      if (progress.discoveries.length === current.value.progress.discoveries.length) return { kind: "changed" };
      const stateIsNewerBook = progress.recipe_hash !== current.value.progress.recipe_hash;
      value = {
        ...(stateIsNewerBook ? value : current.value),
        goal_id: current.value.goal_id, progress, needs_restore: true,
      };
      kind = "merged";
    }
    const raw = JSON.stringify(value);
    if (value.progress.discoveries.length > MAX_DISCOVERIES || exceedsSaveLimit(raw)) return { kind: "unavailable" };
    try { storage.setItem(EXPLORATION_SAVE_KEY, raw); return { kind, raw }; }
    catch { return { kind: "unavailable" }; }
  };
  if (!locks) return transaction();
  try { return await locks.request(EXPLORATION_SAVE_KEY, transaction); }
  catch { return { kind: "unavailable" }; }
}
