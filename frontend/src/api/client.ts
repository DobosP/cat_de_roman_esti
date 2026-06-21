// Typed, same-origin fetch wrappers for every /api endpoint. No API key ever lives
// here — the BFF is server-authoritative and holds the secret. All calls are relative
// ("/api/..."), so they hit the same origin as the served SPA (Vite proxies them in dev).

import type {
  CatalogResponse,
  CreateGameBody,
  GameState,
  HealthResponse,
  HopBody,
  Mode,
} from "./types";

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

// ---------------------------------------------------------------------- endpoints

/** GET /api/health */
export function getHealth(): Promise<HealthResponse> {
  return getJson<HealthResponse>("/api/health");
}

/** GET /api/catalog — menu data. */
export function getCatalog(): Promise<CatalogResponse> {
  return getJson<CatalogResponse>("/api/catalog");
}

/**
 * POST /api/games — new in-memory session for category + difficulty.
 * `exclude` is optional (additive, backward-compatible): when given and more than
 * one candidate exists, the server picks a puzzle whose id != exclude so "Next"
 * advances to a different puzzle (otherwise it gracefully replays the same one).
 */
export function createGame(
  category: string,
  difficulty: Mode,
  exclude?: string,
): Promise<GameState> {
  const body: CreateGameBody = { category, difficulty };
  if (exclude) body.exclude = exclude;
  return postJson<GameState>("/api/games", body);
}

/** GET /api/games/{id} — resume an existing session. */
export function getGame(gameId: string): Promise<GameState> {
  return getJson<GameState>(`/api/games/${encodeURIComponent(gameId)}`);
}

/** POST /api/games/{id}/hop — apply a hop (server validates + scores). */
export function hop(gameId: string, to: string): Promise<GameState> {
  const body: HopBody = { to };
  return postJson<GameState>(
    `/api/games/${encodeURIComponent(gameId)}/hop`,
    body,
  );
}

/** POST /api/games/{id}/reset — restart the same puzzle. */
export function resetGame(gameId: string): Promise<GameState> {
  return postJson<GameState>(
    `/api/games/${encodeURIComponent(gameId)}/reset`,
  );
}

export const api = {
  getHealth,
  getCatalog,
  createGame,
  getGame,
  hop,
  resetGame,
};
