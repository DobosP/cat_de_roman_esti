// Typed, same-origin fetch wrappers for the "Lantul Cuvintelor" word-ladder game.
// Server-authoritative: the chain, optimal distance and validation live in the backend;
// these helpers only shuttle JSON. All URLs are relative (Vite proxies /api in dev).

import { ApiError } from "./client";

const PREFIX = "/api/wordgames/lant";
const JSON_HEADERS = { "Content-Type": "application/json" } as const;

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
  /** Present only when won === true. */
  score?: number;
  share?: string;
}

export interface MoveResult {
  ok: boolean;
  /** Present only when ok === false. */
  last_error?: string;
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
  message?: string;
}

// ---------------------------------------------------------------------- transport
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

// ---------------------------------------------------------------------- endpoints
/** POST /games — start a fresh ladder. */
export function createLant(opts?: {
  seed?: number;
  difficulty?: Difficulty;
  daily?: string;
}): Promise<LantState> {
  const params = new URLSearchParams();
  if (opts?.seed !== undefined) params.set("seed", String(opts.seed));
  if (opts?.difficulty) params.set("difficulty", opts.difficulty);
  if (opts?.daily) params.set("daily", opts.daily);
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
