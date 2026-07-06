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
  discovered_count: number;
  seed_count: number;
  moves: number;
  difficulty: Difficulty;
  target_depth: number;
  won: boolean;
  /** How many nudges the player has revealed (each costs score). */
  hints_used: number;
  /** True once the player is genuinely stuck and a nudge can be requested. */
  hint_available: boolean;
  daily?: string;
  /** Present only when won === true. */
  score?: number;
  share?: string;
}

/** Returned by /combine — the base state plus what this combine produced. */
export interface CombineResult extends AlchimieState {
  discovered: Concept[];
  message: string;
}

/** Returned by /hint — the base state plus the suggested pair (null if none). */
export interface HintResult extends AlchimieState {
  /** The two concepts the nudge suggests combining, or null if unavailable. */
  hint: [Concept, Concept] | null;
  message: string;
}

/** Options for starting a new game. */
export interface CreateOpts {
  seed?: number;
  difficulty?: Difficulty;
  daily?: string;
}

const BASE = "/api/wordgames/alchimie";

/** POST /games — start a new game.
 *
 * `?difficulty=` in {usor,normal,greu} tunes target depth + seed count, `?daily=YYYY-MM-DD`
 * makes a shared deterministic daily instance, and `?seed=` makes it reproducible.
 */
export function createAlchimie(opts: CreateOpts = {}): Promise<AlchimieState> {
  const params = new URLSearchParams();
  if (opts.seed !== undefined) params.set("seed", String(opts.seed));
  if (opts.difficulty) params.set("difficulty", opts.difficulty);
  if (opts.daily) params.set("daily", opts.daily);
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
