// Typed, same-origin fetch wrappers for the "Lantul Cuvintelor" word-ladder game.
// Server-authoritative: the chain, optimal distance and validation live in the backend;
// these helpers only shuttle JSON. All URLs are relative (Vite proxies /api in dev).

import { getJson, postJson } from "./client";

const PREFIX = "/api/wordgames/lant";

// ---------------------------------------------------------------------- types
export interface Concept {
  id: string;
  label: string;
}

export interface PathStep {
  id: string;
  label: string;
  /** Romanian relation label for the edge from the previous step (absent on start). */
  relation?: string;
}

export interface LantTarget {
  id: string;
  label: string;
  description: string;
}

export type Difficulty = "usor" | "normal" | "greu";

export interface LantState {
  game_id: string;
  start: Concept;
  target: LantTarget;
  current: Concept;
  path: PathStep[];
  moves: number;
  optimal: number;
  won: boolean;
  difficulty: Difficulty;
  daily?: string;
  /** Echoed only when the game was started with an explicit category. */
  board_category?: string;
  /** Present only when won === true. */
  score?: number;
  share?: string;
}

export interface MoveResult {
  ok: boolean;
  /** Present only when ok === false. */
  last_error?: string;
  /** Server-authored recovery copy for a correction or a legal dead-end move. */
  message?: string;
  /** True when the accepted hop can no longer reach the target. */
  dead_end?: boolean;
  /** Bounded canonical labels offered after an unknown concept. */
  suggestions?: string[];
  current?: Concept;
  relation?: string;
  path?: PathStep[];
  moves?: number;
  won?: boolean;
  /** Present only when won === true. */
  score?: number;
  share?: string;
}

export interface HintResult {
  hint: Concept | null;
  relation?: string;
  remaining?: number;
  /** How many distinct neighbours lie on a shortest path (>1 => you had a real choice). */
  alternatives?: number;
  /** Named alternatives appear only after a second hint request from the same position. */
  alternatives_labels?: string[];
  message?: string;
}

// ---------------------------------------------------------------------- endpoints
/** POST /games — start a fresh ladder. */
export function createLant(opts?: {
  seed?: number;
  difficulty?: Difficulty;
  daily?: string;
  /** Curated category/theme (ADR-0011); omit for the classic full-graph ladder. */
  category?: string;
}): Promise<LantState> {
  const params = new URLSearchParams();
  if (opts?.seed !== undefined) params.set("seed", String(opts.seed));
  if (opts?.difficulty) params.set("difficulty", opts.difficulty);
  if (opts?.daily) params.set("daily", opts.daily);
  if (opts?.category) params.set("category", opts.category);
  const q = params.toString() ? `?${params.toString()}` : "";
  return postJson<LantState>(`${PREFIX}/games${q}`);
}

/** GET /games/{id} — current state. */
export function getLant(gameId: string): Promise<LantState> {
  return getJson<LantState>(`${PREFIX}/games/${encodeURIComponent(gameId)}`);
}

/** POST /games/{id}/move — type the next linked concept. */
export function moveLant(gameId: string, text: string): Promise<MoveResult> {
  return postJson<MoveResult>(
    `${PREFIX}/games/${encodeURIComponent(gameId)}/move`,
    { text },
  );
}

/** POST /games/{id}/undo — step back one hop (never below the start). */
export function undoLant(gameId: string): Promise<LantState> {
  return postJson<LantState>(
    `${PREFIX}/games/${encodeURIComponent(gameId)}/undo`,
  );
}

/** POST /games/{id}/hint — reveal one neighbour on a shortest path to the target. */
export function hintLant(gameId: string): Promise<HintResult> {
  return postJson<HintResult>(
    `${PREFIX}/games/${encodeURIComponent(gameId)}/hint`,
  );
}

export const lantApi = {
  createLant,
  getLant,
  moveLant,
  undoLant,
  hintLant,
};
