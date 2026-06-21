// Typed, same-origin fetch wrappers for the Alchimie word game. All URLs are relative
// ("/api/wordgames/alchimie/..."), server-authoritative: the target id is only revealed
// by the backend once the player has actually crafted it.

import { ApiError } from "./client";

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

export interface AlchimieState {
  game_id: string;
  target: TargetView;
  inventory: InventoryItem[];
  discovered_count: number;
  seed_count: number;
  moves: number;
  won: boolean;
}

/** Returned by /combine — the base state plus what this combine produced. */
export interface CombineResult extends AlchimieState {
  discovered: Concept[];
  message: string;
}

const JSON_HEADERS = { "Content-Type": "application/json" } as const;
const BASE = "/api/wordgames/alchimie";

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

/** POST /games — start a new game (optional seed for deterministic instances). */
export function createAlchimie(seed?: number): Promise<AlchimieState> {
  const q = seed === undefined ? "" : `?seed=${encodeURIComponent(seed)}`;
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

export const alchimieApi = {
  create: createAlchimie,
  get: getAlchimie,
  combine: combineAlchimie,
  reset: resetAlchimie,
};
