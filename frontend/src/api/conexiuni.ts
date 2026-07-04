// Typed, same-origin fetch wrappers for the Conexiuni (NYT Connections) word game.
// Server-authoritative: the per-category grouping + the full solution are only revealed
// by the backend once the game is won or lost. The client renders what it returns.

import { ApiError } from "./client";

export type Difficulty = "usor" | "normal" | "greu";

export interface Tile {
  id: string;
  label: string;
}

export interface SolvedGroup {
  key: string;
  label: string;
  tiles: Tile[];
}

export interface ConexiuniClue {
  pattern: string;
  message: string;
}

export interface ConexiuniState {
  game_id: string;
  tiles: Tile[];
  solved: SolvedGroup[];
  solved_count: number;
  remaining_groups: number;
  lives: number;
  mistakes: number;
  won: boolean;
  lost: boolean;
  difficulty: Difficulty;
  clues_used: number;
  clue_available: boolean;
  clues: ConexiuniClue[];
  daily?: string;
  // present only once finished:
  score?: number;
  share?: string;
  solution?: SolvedGroup[];
}

/** Result of a /guess call. */
export interface GuessResult {
  ok: true;
  correct: boolean;
  // present only on the terminal winning response:
  category?: { key: string; label: string };
  // correct === false:
  one_away?: boolean;
  // shared public state:
  tiles: Tile[];
  solved: SolvedGroup[];
  solved_count: number;
  remaining_groups: number;
  lives: number;
  mistakes: number;
  won: boolean;
  lost: boolean;
  difficulty: Difficulty;
  clues_used: number;
  clue_available: boolean;
  clues: ConexiuniClue[];
  daily?: string;
  // present on finish (win or loss):
  score?: number;
  share?: string;
  solution?: SolvedGroup[];
}

export interface ClueResult extends ConexiuniState {
  ok: true;
  clue: ConexiuniClue;
}

const JSON_HEADERS = { "Content-Type": "application/json" } as const;
const BASE = "/api/wordgames/conexiuni";

async function parse<T>(res: Response): Promise<T> {
  const text = await res.text();
  let body: unknown = null;
  if (text) {
    try {
      body = JSON.parse(text);
    } catch {
      body = text;
    }
  }
  if (!res.ok) {
    const detail =
      body && typeof body === "object" && "detail" in body
        ? String((body as { detail: unknown }).detail)
        : typeof body === "string" && body
          ? body
          : res.statusText;
    throw new ApiError(res.status, detail || `request failed (${res.status})`);
  }
  return body as T;
}

async function getJson<T>(url: string): Promise<T> {
  return parse<T>(await fetch(url, { headers: { Accept: "application/json" } }));
}

async function postJson<T>(url: string, body?: unknown): Promise<T> {
  return parse<T>(
    await fetch(url, {
      method: "POST",
      headers: JSON_HEADERS,
      body: body === undefined ? undefined : JSON.stringify(body),
    }),
  );
}

export interface CreateOpts {
  seed?: number;
  difficulty?: Difficulty;
  daily?: string;
}

/** POST /games — start a new board. */
export function createConexiuni(opts: CreateOpts = {}): Promise<ConexiuniState> {
  const q = new URLSearchParams();
  if (opts.seed !== undefined) q.set("seed", String(opts.seed));
  if (opts.difficulty) q.set("difficulty", opts.difficulty);
  if (opts.daily) q.set("daily", opts.daily);
  const qs = q.toString();
  return postJson<ConexiuniState>(`${BASE}/games${qs ? `?${qs}` : ""}`);
}

/** GET /games/{id} — full current state (solution hidden until won/lost). */
export function getConexiuni(gameId: string): Promise<ConexiuniState> {
  return getJson<ConexiuniState>(`${BASE}/games/${encodeURIComponent(gameId)}`);
}

/** The board is always 4 groups of 4; a guess is exactly this many distinct tiles. */
export const GROUP_SIZE = 4;

/**
 * POST /games/{id}/guess — submit exactly 4 distinct tile ids.
 *
 * The server is authoritative, but we reject a malformed selection up front (wrong
 * count or duplicates) so the UI can't waste a life on an input the backend would 400.
 */
export function guessConexiuni(gameId: string, ids: string[]): Promise<GuessResult> {
  const distinct = new Set(ids);
  if (ids.length !== GROUP_SIZE || distinct.size !== GROUP_SIZE) {
    return Promise.reject(
      new ApiError(400, `Alege exact ${GROUP_SIZE} concepte distincte`),
    );
  }
  return postJson<GuessResult>(
    `${BASE}/games/${encodeURIComponent(gameId)}/guess`,
    { ids: [...ids] },
  );
}

/** POST /games/{id}/clue — reveal one redacted remaining category-label pattern. */
export function clueConexiuni(gameId: string): Promise<ClueResult> {
  return postJson<ClueResult>(`${BASE}/games/${encodeURIComponent(gameId)}/clue`);
}

export const conexiuniApi = {
  create: createConexiuni,
  get: getConexiuni,
  guess: guessConexiuni,
  clue: clueConexiuni,
};
