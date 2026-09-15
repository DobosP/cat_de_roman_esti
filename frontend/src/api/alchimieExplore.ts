import { getJson, postJson } from "./client";
import type { Concept } from "./alchimie";

export interface ExplorationProgress {
  world_id: string;
  recipe_hash: string;
  discoveries: [string, string][];
}

export interface ExplorationItem extends Concept {
  description: string;
  parents: [Concept, Concept] | null;
  explanation: string | null;
  sources: string[];
  status: "active" | "depleted" | "final";
  ready: boolean;
}

export interface ExplorationState {
  game_id: string;
  revision: number;
  mode: "explore";
  world: { id: string; title: string; description: string; total_concepts: number; total_recipes: number };
  inventory: ExplorationItem[];
  discovered_count: number;
  seed_count: number;
  complete: boolean;
  goals: { id: string; title: string; label: string; completed: boolean; target_id: string | null }[];
  goal_id: string | null;
  hint: {
    stage: "output" | "pair" | "complete";
    message: string;
    output: { label: string } | null;
    pair: [Concept, Concept] | null;
  } | null;
  progress: ExplorationProgress;
  compatible_recipe_hashes: string[];
  /** Only pairs observed empty in this live session; older responses may omit it. */
  empty_pairs?: [string, string][];
  unlocked: { id: string; title: string; after_discoveries: number }[];
  next_unlock: { title: string; after_discoveries: number; remaining: number } | null;
}

export interface ExplorationResult extends ExplorationState {
  discovered: Concept[];
  result: Concept | null;
  message: string;
  already_known: boolean;
  supplied: Concept[];
}

const BASE = "/api/alchimie/explore";
const gamePath = (gameId: string) => `${BASE}/${encodeURIComponent(gameId)}`;

export const explorationApi = {
  create: (options: { progress?: ExplorationProgress; goal_id?: string | null } = {}) =>
    postJson<ExplorationState>(BASE, options),
  get: (gameId: string) => getJson<ExplorationState>(gamePath(gameId)),
  combine: (gameId: string, a: string, b: string) =>
    postJson<ExplorationResult>(`${gamePath(gameId)}/combine`, { a, b }),
  hint: (gameId: string) => postJson<ExplorationState>(`${gamePath(gameId)}/hint`, {}),
  goal: (gameId: string, goalId: string | null) =>
    postJson<ExplorationState>(`${gamePath(gameId)}/goal`, { goal_id: goalId }),
};
