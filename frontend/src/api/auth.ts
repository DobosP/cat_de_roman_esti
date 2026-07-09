// api/auth.ts — account + saved-progress transport (accounts ON only).
//
// Separate from api/client.ts on purpose: the account endpoints need same-origin session
// cookies + the CSRF token echoed as X-CSRFToken (Django/DRF SessionAuthentication). The
// anonymous game client stays cookie/CSRF-free. GET /api/me seeds the csrftoken cookie.

export interface AuthUser {
  id: number;
  email: string;
  name: string;
  avatar: string;
  consent_completed: boolean;
  can_save_progress: boolean;
  is_minor: boolean;
  parental_consent_required: boolean;
}

export interface MeResponse {
  accounts_enabled: boolean;
  authenticated: boolean;
  user: AuthUser | null;
  min_self_consent_age?: number;
}

export class AuthError extends Error {
  status: number;
  body: unknown;
  constructor(message: string, status: number, body: unknown) {
    super(message);
    this.name = "AuthError";
    this.status = status;
    this.body = body;
  }
}

function getCookie(name: string): string | null {
  const prefix = `${name}=`;
  for (const part of document.cookie ? document.cookie.split(";") : []) {
    const c = part.trim();
    if (c.startsWith(prefix)) return decodeURIComponent(c.slice(prefix.length));
  }
  return null;
}

async function request<T>(method: string, path: string, body?: unknown): Promise<T> {
  const headers: Record<string, string> = { "Content-Type": "application/json" };
  if (method !== "GET") {
    const token = getCookie("csrftoken");
    if (token) headers["X-CSRFToken"] = token;
  }
  const res = await fetch(path, {
    method,
    credentials: "same-origin",
    headers,
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  const data = (await res.json().catch(() => null)) as T & { detail?: unknown };
  if (!res.ok) {
    const detail = typeof data?.detail === "string" ? data.detail : res.statusText;
    throw new AuthError(detail, res.status, data);
  }
  return data;
}

export const getMe = (): Promise<MeResponse> => request<MeResponse>("GET", "/api/me");

export const postAuth = <T = unknown>(path: string, body?: unknown): Promise<T> =>
  request<T>("POST", path, body);

export const logout = (): Promise<{ ok: boolean }> =>
  request<{ ok: boolean }>("POST", "/api/auth/logout");

export interface ConsentResponse {
  status: "ok" | "parental_consent_required";
  user: AuthUser;
  min_self_consent_age?: number;
}

export const submitConsent = (birthYear: number, accept: boolean): Promise<ConsentResponse> =>
  request<ConsentResponse>("POST", "/api/me/consent", {
    birth_year: birthYear,
    accept_privacy: accept,
    accept_tos: accept,
  });

export const deleteAccount = (): Promise<{ ok: boolean }> =>
  request<{ ok: boolean }>("POST", "/api/me/delete");

/** Start the Google OAuth flow (full-page redirect handled server-side by allauth). */
export function loginWithGoogle(): void {
  window.location.href = "/accounts/google/login/?process=login";
}
