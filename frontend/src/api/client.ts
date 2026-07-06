// api/client.ts — the app's single HTTP transport, built on @roedu/ui's shared
// createApiClient (replaces the per-game fetch plumbing). Same-origin BFF: Vite
// proxies /api in dev, FastAPI serves the SPA in prod. No secrets client-side.
//
// FastAPI signals user-facing failures as {"detail": "..."} — normalize that into
// ApiError.message once, here, so screens can just show err.message.

import { createApiClient, ApiError } from "@roedu/ui";

const client = createApiClient({ baseUrl: "" });

function rethrowFriendly(err: unknown): never {
  if (err instanceof ApiError) {
    const detail = (err.body as { detail?: unknown } | null)?.detail;
    if (typeof detail === "string" && detail.trim()) {
      throw new ApiError(detail, err.status, err.body);
    }
  }
  throw err;
}

export async function getJson<T>(path: string): Promise<T> {
  try {
    return await client.get<T>(path);
  } catch (err) {
    rethrowFriendly(err);
  }
}

export async function postJson<T>(path: string, body?: unknown): Promise<T> {
  try {
    return await client.post<T>(path, body);
  } catch (err) {
    rethrowFriendly(err);
  }
}

export { ApiError };
