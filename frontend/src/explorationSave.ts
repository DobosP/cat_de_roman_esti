import type { ExplorationProgress, ExplorationState } from "./api/alchimieExplore";

export const EXPLORATION_SAVE_KEY = "cat_alchimie_exploration_v1";
const MAX_SAVE_BYTES = 64 * 1024;
type SaveStorage = Pick<Storage, "getItem" | "setItem">;

export interface ExplorationSave {
  version: 1;
  game_id: string;
  revision: number;
  progress: ExplorationProgress;
  goal_id: string | null;
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

export function readExplorationSave(storage: SaveStorage | null = browserStorage()): SaveRead {
  if (!storage) return { kind: "unavailable", raw: null };
  let raw: string | null;
  try { raw = storage.getItem(EXPLORATION_SAVE_KEY); } catch { return { kind: "unavailable", raw: null }; }
  if (raw === null) return { kind: "empty", raw: null };
  if (raw.length > MAX_SAVE_BYTES) return { kind: "invalid", raw };
  try {
    const value = JSON.parse(raw) as ExplorationSave;
    if (value?.version !== 1 || !validId(value.game_id) ||
      !Number.isSafeInteger(value.revision) || value.revision < 0 ||
      (value.goal_id !== null && !validId(value.goal_id)) ||
      (value.needs_restore !== undefined && typeof value.needs_restore !== "boolean") ||
      !validId(value.progress?.world_id) || !/^[a-f0-9]{64}$/.test(value.progress.recipe_hash) ||
      !Array.isArray(value.progress.discoveries) ||
      value.progress.discoveries.length > 128 || value.progress.discoveries.some((pair) =>
        !Array.isArray(pair) || pair.length !== 2 || !pair.every(validId) || pair[0] === pair[1])) {
      return { kind: "invalid", raw };
    }
    return { kind: "saved", value, raw };
  } catch { return { kind: "invalid", raw }; }
}

type SaveResult = { kind: "saved" | "merged"; raw: string } | { kind: "changed" | "unavailable" };

/** Preserve both valid recipe sequences if separate live sessions advanced at once. */
export function mergeExplorationProgress(a: ExplorationProgress, b: ExplorationProgress): ExplorationProgress | null {
  if (a.world_id !== b.world_id || a.recipe_hash !== b.recipe_hash) return null;
  const pairs = new Set<string>();
  const discoveries: [string, string][] = [];
  for (const pair of [...a.discoveries, ...b.discoveries]) {
    const key = JSON.stringify([...pair].sort());
    if (pairs.has(key)) continue;
    pairs.add(key);
    discoveries.push(pair);
  }
  return discoveries.length <= 128 ? { world_id: a.world_id, recipe_hash: a.recipe_hash, discoveries } : null;
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
    };
    let kind: "saved" | "merged" = "saved";
    if (current.raw !== expectedRaw || (current.kind === "saved" && current.value.game_id === state.game_id && current.value.revision > state.revision)) {
      if (current.kind !== "saved") return { kind: "changed" };
      const progress = mergeExplorationProgress(current.value.progress, state.progress);
      if (!progress) return { kind: "changed" };
      if (progress.discoveries.length === current.value.progress.discoveries.length) return { kind: "changed" };
      value = { ...current.value, progress, needs_restore: true };
      kind = "merged";
    }
    const raw = JSON.stringify(value);
    if (raw.length > MAX_SAVE_BYTES) return { kind: "unavailable" };
    try { storage.setItem(EXPLORATION_SAVE_KEY, raw); return { kind, raw }; }
    catch { return { kind: "unavailable" }; }
  };
  if (!locks) return transaction();
  try { return await locks.request(EXPLORATION_SAVE_KEY, transaction); }
  catch { return { kind: "unavailable" }; }
}
