// Typed API wrappers for the "Cald sau Rece" (contexto) word game.
// Server-authoritative: the secret target is never sent until the game is won or
// given up. All URLs are relative ("/api/..."), so they hit the SPA's origin.

import { getJson, postJson } from "./client";
export { ApiError } from "./client";

// ----------------------------------------------------------------------- types

export type Temperature =
  | "Gasit"
  | "Fierbinte"
  | "Cald"
  | "Caldut"
  | "Rece"
  | "Inghetat";

export interface Guess {
  id: string;
  label: string;
  distance: number;
  /** 1 is the hidden target; unreachable guesses sort after the reachable set. */
  rank: number;
  temperature: Temperature;
  /** 0..100 — how close (beats this % of reachable concepts). */
  closeness: number;
}

export interface RevealedTarget {
  id: string;
  label: string;
  description: string;
}

export type Difficulty = "usor" | "normal" | "greu";

export interface CategoryClue {
  category: {
    key: string;
    label: string;
  };
  message: string;
}

export interface WarmClue {
  label: string;
  /** Strictly better than the player's best rank when the clue was issued; never 1. */
  rank: number;
  message: string;
}

export type NextClueKind = "category" | "warmer";

/** Full game state (GET /games/{id} and POST /games). */
export interface ContextoState {
  game_id: string;
  attempts: number;
  won: boolean;
  gave_up: boolean;
  reachable_count: number;
  difficulty: Difficulty;
  clues_used: number;
  clue_available: boolean;
  /** The next bounded clue stage; absent when no safe clue remains. */
  next_clue_kind?: NextClueKind;
  /** Present only after the player asks for the clue. */
  clue?: CategoryClue;
  /** Present only after the server issues one guaranteed-warmer, non-target word. */
  warm_clue?: WarmClue;
  /** Present only for a "Provocarea zilei" game (YYYY-MM-DD). */
  daily?: string;
  /** Echoed only when the game was started with an explicit category. */
  board_category?: string;
  /** Past guesses, sorted best-first by the server. */
  guesses: Guess[];
  /** Present only once won or given up. */
  target?: RevealedTarget;
  /** Present only once won (higher = better). */
  score?: number;
  /** Present only once won: a shareable, Wordle-style line. */
  share?: string;
}

/** A rejected guess (unknown concept) — not counted as an attempt. */
export interface GuessRejected {
  ok: false;
  message: string;
  /** Bounded, server-filtered labels; the hidden target is never included. */
  suggestions: string[];
  guesses: Guess[];
  attempts: number;
  won: boolean;
  reachable_count: number;
  clues_used: number;
  clue_available: boolean;
  next_clue_kind?: NextClueKind;
  clue?: CategoryClue;
  warm_clue?: WarmClue;
}

/** An accepted guess. */
export interface GuessAccepted {
  ok: true;
  /** Present only when the server confidently accepted a corrected label. */
  message?: string;
  guess: Guess;
  guesses: Guess[];
  attempts: number;
  won: boolean;
  reachable_count: number;
  clues_used: number;
  clue_available: boolean;
  next_clue_kind?: NextClueKind;
  clue?: CategoryClue;
  warm_clue?: WarmClue;
  target?: RevealedTarget;
  /** Present only once won (higher = better). */
  score?: number;
  /** Present only once won: a shareable, Wordle-style line. */
  share?: string;
}

export type GuessResult = GuessRejected | GuessAccepted;

export interface ClueResult extends ContextoState {
  ok: true;
  clue_kind: NextClueKind;
  /** Direct category result for the first, unthemed clue stage. */
  category?: CategoryClue["category"];
  /** Direct warmer-word result for the second stage. */
  word?: WarmClue;
  message: string;
}

// --------------------------------------------------------------------- endpoints

const BASE = "/api/wordgames/contexto";

export interface CreateOpts {
  seed?: number;
  difficulty?: Difficulty;
  /** "YYYY-MM-DD" — start the deterministic daily challenge for that date. */
  daily?: string;
  /** Curated category/theme (ADR-0011); omit for the classic full-graph game. */
  category?: string;
}

/** POST /games — start a new game with a hidden secret target. */
export function createGame(opts: CreateOpts = {}): Promise<ContextoState> {
  const params = new URLSearchParams();
  if (opts.seed !== undefined) params.set("seed", String(opts.seed));
  if (opts.difficulty) params.set("difficulty", opts.difficulty);
  if (opts.daily) params.set("daily", opts.daily);
  if (opts.category) params.set("category", opts.category);
  const q = params.toString();
  return postJson<ContextoState>(`${BASE}/games${q ? `?${q}` : ""}`);
}

/** GET /games/{id} — resume an existing game (target hidden unless finished). */
export function getGame(gameId: string): Promise<ContextoState> {
  return getJson<ContextoState>(
    `${BASE}/games/${encodeURIComponent(gameId)}`,
  );
}

/** POST /games/{id}/guess — submit a concept; server scores closeness. */
export function submitGuess(
  gameId: string,
  text: string,
): Promise<GuessResult> {
  return postJson<GuessResult>(
    `${BASE}/games/${encodeURIComponent(gameId)}/guess`,
    { text },
  );
}

/** POST /games/{id}/clue — reveal the broad target category, not the target itself. */
export function requestClue(gameId: string): Promise<ClueResult> {
  return postJson<ClueResult>(
    `${BASE}/games/${encodeURIComponent(gameId)}/clue`,
  );
}

/** POST /games/{id}/giveup — reveal the target and end the game. */
export function giveUp(gameId: string): Promise<ContextoState> {
  return postJson<ContextoState>(
    `${BASE}/games/${encodeURIComponent(gameId)}/giveup`,
  );
}

export const contextoApi = {
  createGame,
  getGame,
  submitGuess,
  requestClue,
  giveUp,
};
