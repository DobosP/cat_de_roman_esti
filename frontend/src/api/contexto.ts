// Typed, same-origin fetch wrappers for the "Cald sau Rece" (contexto) word game.
// Server-authoritative: the secret target is never sent until the game is won or
// given up. All URLs are relative ("/api/..."), so they hit the SPA's origin.

export class ApiError extends Error {
  readonly status: number;
  constructor(status: number, message: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

const JSON_HEADERS = { "Content-Type": "application/json" } as const;

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

/** Full game state (GET /games/{id} and POST /games). */
export interface ContextoState {
  game_id: string;
  attempts: number;
  won: boolean;
  gave_up: boolean;
  reachable_count: number;
  difficulty: Difficulty;
  /** Present only for a "Provocarea zilei" game (YYYY-MM-DD). */
  daily?: string;
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
  guesses: Guess[];
  attempts: number;
  won: boolean;
  reachable_count: number;
}

/** An accepted guess. */
export interface GuessAccepted {
  ok: true;
  guess: Guess;
  guesses: Guess[];
  attempts: number;
  won: boolean;
  reachable_count: number;
  target?: RevealedTarget;
  /** Present only once won (higher = better). */
  score?: number;
  /** Present only once won: a shareable, Wordle-style line. */
  share?: string;
}

export type GuessResult = GuessRejected | GuessAccepted;

// --------------------------------------------------------------------- endpoints

const BASE = "/api/wordgames/contexto";

export interface CreateOpts {
  seed?: number;
  difficulty?: Difficulty;
  /** "YYYY-MM-DD" — start the deterministic daily challenge for that date. */
  daily?: string;
}

/** POST /games — start a new game with a hidden secret target. */
export function createGame(opts: CreateOpts = {}): Promise<ContextoState> {
  const params = new URLSearchParams();
  if (opts.seed !== undefined) params.set("seed", String(opts.seed));
  if (opts.difficulty) params.set("difficulty", opts.difficulty);
  if (opts.daily) params.set("daily", opts.daily);
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
  giveUp,
};
