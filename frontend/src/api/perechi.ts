// Typed, same-origin client for Perechi. Pair mappings, source provenance and scoring
// stay server-side; the UI only renders solved pairs and the one explicitly earned hint.

import { ApiError, getJson, postJson } from "./client";

export interface PerechiTile {
  id: string;
  label: string;
  solved: boolean;
}

export interface PerechiConcept {
  id: string;
  label: string;
}

export interface PerechiPair {
  tiles: PerechiConcept[];
  label: string;
}

export interface PerechiState {
  game_id: string;
  tiles: PerechiTile[];
  solved_pairs: PerechiPair[];
  solved_count: number;
  remaining_pairs: number;
  mistakes: number;
  remaining_mistakes: number;
  actions: number;
  hint_available: boolean;
  hints_used: number;
  won: boolean;
  lost: boolean;
  hint?: PerechiPair;
  daily?: string;
  board_category?: string;
  // Terminal-only, authored by the server.
  score?: number;
  share?: string;
  solution?: PerechiPair[];
}

export interface PerechiMatchResult extends PerechiState {
  ok: true;
  correct: boolean;
  repeated?: boolean;
  pair?: PerechiPair;
}

export interface PerechiHintResult extends PerechiState {
  ok: true;
  hint: PerechiPair;
}

export interface CreatePerechiOpts {
  seed?: number;
  daily?: string;
  category?: string;
  starter?: boolean;
  previousGameId?: string;
}

const BASE = "/api/wordgames/perechi";

export function createPerechi(opts: CreatePerechiOpts = {}): Promise<PerechiState> {
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
  return postJson<PerechiState>(`${BASE}/games${suffix ? `?${suffix}` : ""}`);
}

export function getPerechi(gameId: string): Promise<PerechiState> {
  return getJson<PerechiState>(`${BASE}/games/${encodeURIComponent(gameId)}`);
}

export function matchPerechi(
  gameId: string,
  ids: readonly string[],
): Promise<PerechiMatchResult> {
  const clean = ids.map((id) => id.trim());
  if (clean.length !== 2 || clean.some((id) => !id) || new Set(clean).size !== 2) {
    return Promise.reject(
      new ApiError("Alege exact două cuvinte distincte.", 400, {
        detail: "Alege exact două cuvinte distincte.",
      }),
    );
  }
  return postJson<PerechiMatchResult>(
    `${BASE}/games/${encodeURIComponent(gameId)}/match`,
    { ids: clean },
  );
}

export function hintPerechi(gameId: string): Promise<PerechiHintResult> {
  return postJson<PerechiHintResult>(
    `${BASE}/games/${encodeURIComponent(gameId)}/hint`,
  );
}

export const perechiApi = {
  create: createPerechi,
  get: getPerechi,
  match: matchPerechi,
  hint: hintPerechi,
};
