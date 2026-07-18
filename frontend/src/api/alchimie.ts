// Typed, same-origin fetch wrappers for the Alchimie word game. All URLs are relative
// ("/api/wordgames/alchimie/..."), server-authoritative: the target id is only revealed
// by the backend once the player has actually crafted it.

import { getJson, postJson } from "./client";

export interface Concept {
  id: string;
  label: string;
}

/** An inventory entry; `parents` is the two concepts it was combined FROM (null for seeds). */
export interface InventoryItem {
  id: string;
  label: string;
  parents: [Concept, Concept] | null;
  /** Recently added to the bounded workspace. */
  recent: boolean;
  /** Still participates in at least one recipe with an unseen result. */
  useful: boolean;
  /** A useful recipe's other ingredient is already owned. */
  ready: boolean;
  /** Kept for lineage/"Toate", but automatically left out of active views. */
  depleted: boolean;
}

export interface InventorySummary {
  active: number;
  depleted: number;
  total: number;
}

export interface RecipeSummary {
  pairs: number;
  routes: number;
  max_results: number;
}

export interface TargetView {
  /** Secret id — null until `revealed` (i.e. until the player wins). */
  id: string | null;
  label: string;
  description: string;
  revealed: boolean;
}

export type Difficulty = "usor" | "normal" | "greu";

export interface AlchimieState {
  game_id: string;
  target: TargetView;
  inventory: InventoryItem[];
  inventory_summary: InventorySummary;
  /** Only bounded counts are public; recipe ids/routes stay server-side. */
  recipe_summary: RecipeSummary;
  discovered_count: number;
  /** Number of distinct unordered pairs tried in this bounded session. */
  attempted_count: number;
  seed_count: number;
  moves: number;
  difficulty: Difficulty;
  target_depth: number;
  won: boolean;
  /** How many nudges the player has revealed (each costs score). */
  hints_used: number;
  /** True once the player is genuinely stuck and a nudge can be requested. */
  hint_available: boolean;
  /** What the next progressive hint will reveal. */
  hint_stage: "output" | "pair";
  daily?: string;
  /** Server-selected board theme; playable Alchimie boards are always themed. */
  board_category?: string;
  /** Present only when won === true. */
  score?: number;
  share?: string;
}

/** Returned by /combine — the base state plus what this combine produced. */
export interface CombineResult extends AlchimieState {
  discovered: Concept[];
  /** True when this unordered pair was already remembered and cost no move. */
  already_tried: boolean;
  message: string;
}

/** Returned by /hint — the base state plus the suggested pair (null if none). */
export interface HintResult extends AlchimieState {
  /** The two concepts the nudge suggests combining, or null if unavailable. */
  hint: [Concept, Concept] | null;
  hint_kind: "output" | "category" | "pair" | "none";
  /** First hint: label only, never the private output/target id. */
  hint_output: { label: string } | null;
  message: string;
}

/** Options for starting a new game. */
export interface CreateOpts {
  seed?: number;
  difficulty?: Difficulty;
  daily?: string;
  /** Preferred theme; omit to let the server deterministically choose one. */
  category?: string;
}

const BASE = "/api/wordgames/alchimie";

/** POST /games — start a new game.
 *
 * `?difficulty=` in {usor,normal,greu} tunes target depth + seed count, `?daily=YYYY-MM-DD`
 * makes a shared deterministic daily instance, `?seed=` makes it reproducible, and an
 * omitted `?category=` lets the server choose a bounded theme rather than using the full graph.
 */
export function createAlchimie(opts: CreateOpts = {}): Promise<AlchimieState> {
  const params = new URLSearchParams();
  if (opts.seed !== undefined) params.set("seed", String(opts.seed));
  if (opts.difficulty) params.set("difficulty", opts.difficulty);
  if (opts.daily) params.set("daily", opts.daily);
  if (opts.category) params.set("category", opts.category);
  const q = params.toString() ? `?${params.toString()}` : "";
  return postJson<AlchimieState>(`${BASE}/games${q}`);
}

/** GET /games/{id} — full current state. */
export function getAlchimie(gameId: string): Promise<AlchimieState> {
  return getJson<AlchimieState>(`${BASE}/games/${encodeURIComponent(gameId)}`);
}

/** POST /games/{id}/combine — combine two owned concepts. */
export function combineAlchimie(
  gameId: string,
  a: string,
  b: string,
): Promise<CombineResult> {
  return postJson<CombineResult>(
    `${BASE}/games/${encodeURIComponent(gameId)}/combine`,
    { a, b },
  );
}

/** POST /games/{id}/reset — back to the original seed inventory (same target). */
export function resetAlchimie(gameId: string): Promise<AlchimieState> {
  return postJson<AlchimieState>(
    `${BASE}/games/${encodeURIComponent(gameId)}/reset`,
  );
}

/** POST /games/{id}/hint — reveal a useful pair after several fruitless combines. */
export function hintAlchimie(gameId: string): Promise<HintResult> {
  return postJson<HintResult>(
    `${BASE}/games/${encodeURIComponent(gameId)}/hint`,
  );
}

export const alchimieApi = {
  create: createAlchimie,
  createGame: createAlchimie,
  get: getAlchimie,
  combine: combineAlchimie,
  reset: resetAlchimie,
  hint: hintAlchimie,
};

export { ApiError } from "./client";
