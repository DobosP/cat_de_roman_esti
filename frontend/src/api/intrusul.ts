// Typed, same-origin client for Intrusul. The server owns the answer and score;
// before the round ends the browser only receives visible tiles and earned feedback.

import { ApiError, getJson, postJson } from "./client";

export type Difficulty = "usor" | "normal" | "greu";

export interface IntrusulTile {
  id: string;
  label: string;
}

export interface IntrusulClue {
  label: string;
  message: string;
}

export interface IntrusulSolution {
  intruder: IntrusulTile;
  group: {
    label: string;
    tiles: IntrusulTile[];
  };
}

export interface IntrusulState {
  game_id: string;
  tiles: IntrusulTile[];
  wrong_ids: string[];
  attempts: number;
  mistakes: number;
  remaining_mistakes: number;
  won: boolean;
  lost: boolean;
  difficulty: Difficulty;
  hints_used: number;
  hint_available: boolean;
  clue?: IntrusulClue;
  daily?: string;
  board_category?: string;
  // Terminal-only, authored by the server.
  score?: number;
  share?: string;
  solution?: IntrusulSolution;
}

export interface IntrusulGuessResult extends IntrusulState {
  ok: true;
  correct: boolean;
  already_tried: boolean;
  message: string;
}

export interface IntrusulHintResult extends IntrusulState {
  ok: true;
}

export interface CreateIntrusulOpts {
  seed?: number;
  daily?: string;
  category?: string;
  starter?: boolean;
  previousGameId?: string;
}

const BASE = "/api/wordgames/intrusul";

export function createIntrusul(opts: CreateIntrusulOpts = {}): Promise<IntrusulState> {
  const query = new URLSearchParams();
  if (opts.seed !== undefined) query.set("seed", String(opts.seed));
  if (opts.daily) query.set("daily", opts.daily);
  if (opts.category) query.set("category", opts.category);
  // Shared dailies deliberately omit personalization inputs.
  if (!opts.daily && opts.starter !== undefined) {
    query.set("starter", opts.starter ? "1" : "0");
  }
  if (!opts.daily && opts.previousGameId) {
    query.set("previous_game_id", opts.previousGameId);
  }
  const suffix = query.toString();
  return postJson<IntrusulState>(`${BASE}/games${suffix ? `?${suffix}` : ""}`);
}

export function getIntrusul(gameId: string): Promise<IntrusulState> {
  return getJson<IntrusulState>(`${BASE}/games/${encodeURIComponent(gameId)}`);
}

export function guessIntrusul(
  gameId: string,
  id: string,
): Promise<IntrusulGuessResult> {
  const selected = id.trim();
  if (!selected) {
    return Promise.reject(new ApiError("Alege un cuvânt.", 400, { detail: "Alege un cuvânt." }));
  }
  return postJson<IntrusulGuessResult>(
    `${BASE}/games/${encodeURIComponent(gameId)}/guess`,
    { id: selected },
  );
}

export function hintIntrusul(gameId: string): Promise<IntrusulHintResult> {
  return postJson<IntrusulHintResult>(
    `${BASE}/games/${encodeURIComponent(gameId)}/hint`,
  );
}

export const intrusulApi = {
  create: createIntrusul,
  get: getIntrusul,
  guess: guessIntrusul,
  hint: hintIntrusul,
};
