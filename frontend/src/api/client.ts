// Shared HTTP error type for the word-game API wrappers. Each game's api/<game>.ts has
// its own tiny fetch helpers and throws this on a non-2xx response so screens can show a
// status-aware message. The BFF is server-authoritative; no secrets ever live client-side.

export class ApiError extends Error {
  readonly status: number;
  constructor(status: number, message: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}
