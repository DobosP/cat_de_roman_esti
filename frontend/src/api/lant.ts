// Typed, same-origin fetch wrappers for the "Lantul Cuvintelor" word-ladder game.
// Server-authoritative: the chain, optimal distance and validation live in the backend;
// these helpers only shuttle JSON. All URLs are relative (Vite proxies /api in dev).

import type { PerfectRoundCounters } from "./round";
import { getJson, postJson } from "./client";

const PREFIX = "/api/wordgames/lant";
const pendingGiveUps = new Map<string, Promise<LantState>>();

// ---------------------------------------------------------------------- types
export interface Concept {
  id: string;
  label: string;
}

/** One ID-free, currently legal server-authored hop. Route membership stays private. */
export interface LantChoice {
  label: string;
  relation: string;
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

export type LantProgressKind =
  | "closer"
  | "lateral"
  | "farther"
  | "dead_end"
  | "won";

export interface LantProgress {
  kind: LantProgressKind;
  message: string;
}

export interface LantState extends PerfectRoundCounters {
  game_id: string;
  start: Concept;
  target: LantTarget;
  current: Concept;
  path: PathStep[];
  moves: number;
  optimal: number;
  won: boolean;
  /** Present when the server has recorded an explicit give-up. */
  gave_up?: true;
  /** Enabled, eligible daily rounds report an explicit give-up to the server. */
  can_report_give_up?: true;
  /** Already requested help for this position; reading never escalates it. */
  earned_hint?: HintResult;
  difficulty: Difficulty;
  /** Four to six safe local hops when available; never the full route corridor. */
  choices: LantChoice[];
  /** Easy-mode recovery signal; the private consecutive-move count is never exposed. */
  backtrack_recommended: boolean;
  daily?: string;
  /** Echoed only when the game was started with an explicit category. */
  board_category?: string;
  /** Present only when won === true. */
  score?: number;
  share?: string;
}

export interface MoveResult extends PerfectRoundCounters {
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
  choices?: LantChoice[];
  /** Easy/Normal coarse direction only; never an exact distance or route marker. */
  progress?: LantProgress;
  backtrack_recommended?: boolean;
  /** Present only when won === true. */
  score?: number;
  share?: string;
}

export interface HintResult extends PerfectRoundCounters {
  hint: Concept | null;
  /** Voluntary escalation, or an explicit free-undo recovery from a revisit trap. */
  stage?: "direction" | "alternatives" | "hop" | "backtrack";
  relation?: string;
  remaining?: number;
  /** How many distinct neighbours lie on a shortest path (>1 => you had a real choice). */
  alternatives?: number;
  /** Named alternatives appear from the second voluntary-help stage in the session. */
  alternatives_labels?: string[];
  alternatives_choices?: LantChoice[];
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
export async function getLant(gameId: string): Promise<LantState> {
  const giveUp = pendingGiveUps.get(gameId);
  if (giveUp) {
    try {
      await giveUp;
    } catch {
      // The POST may have committed even if its response was lost.
    }
  }
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

/** POST /games/{id}/giveup — report an explicit give-up for an eligible daily round. */
export function giveUpLant(gameId: string): Promise<LantState> {
  const pending = pendingGiveUps.get(gameId);
  if (pending) return pending;

  const request = postJson<LantState>(`${PREFIX}/games/${encodeURIComponent(gameId)}/giveup`)
    .finally(() => { pendingGiveUps.delete(gameId); });
  pendingGiveUps.set(gameId, request);
  return request;
}

/** POST /games/{id}/hint — progressively reveal direction, alternatives, then one hop. */
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
