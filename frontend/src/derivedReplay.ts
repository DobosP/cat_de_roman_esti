// Bounded replay continuity for the two derived games.
//
// The browser remembers only the opaque id of the last completed non-daily
// server session. The server resolves that id back to its private four-source
// ring; source/catalog ids and answers never enter browser storage.

export type DerivedReplayGame = "intrusul" | "perechi";

const STORAGE_KEY = "cat_derived_replay_v1";
const STORAGE_VERSION = 1;
const GAMES: readonly DerivedReplayGame[] = ["intrusul", "perechi"];
const MAX_SESSION_ID_LENGTH = 128;

type ReplayIds = Partial<Record<DerivedReplayGame, string>>;

interface StoredReplayIds {
  version: typeof STORAGE_VERSION;
  ids: ReplayIds;
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function hasControlCharacter(value: string): boolean {
  return Array.from(value).some((character) => {
    const code = character.charCodeAt(0);
    return code < 32 || code === 127;
  });
}

function normalizeSessionId(value: unknown): string | null {
  if (typeof value !== "string") return null;
  const id = value.trim();
  if (!id || id.length > MAX_SESSION_ID_LENGTH || hasControlCharacter(id)) {
    return null;
  }
  return id;
}

function normalizeIds(value: unknown): ReplayIds {
  if (!isRecord(value)) return {};
  const ids: ReplayIds = {};
  for (const game of GAMES) {
    const id = normalizeSessionId(value[game]);
    if (id) ids[game] = id;
  }
  return ids;
}

function read(): { ids: ReplayIds; migrate: boolean } {
  if (typeof localStorage === "undefined") return { ids: {}, migrate: false };
  try {
    const parsed: unknown = JSON.parse(localStorage.getItem(STORAGE_KEY) || "{}");
    if (
      isRecord(parsed) &&
      parsed.version === STORAGE_VERSION &&
      isRecord(parsed.ids)
    ) {
      return { ids: normalizeIds(parsed.ids), migrate: false };
    }
    // Accept the unversioned draft shape once and rewrite it into the versioned
    // document. Only the two allow-listed game keys survive the migration.
    if (isRecord(parsed) && !("version" in parsed) && !("ids" in parsed)) {
      return { ids: normalizeIds(parsed), migrate: true };
    }
  } catch {
    // Corrupt or unavailable storage is equivalent to no replay memory.
  }
  return { ids: {}, migrate: false };
}

function write(ids: ReplayIds): void {
  if (typeof localStorage === "undefined") return;
  const document: StoredReplayIds = {
    version: STORAGE_VERSION,
    ids: normalizeIds(ids),
  };
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(document));
  } catch {
    // Replay diversity is best-effort when browser storage is unavailable.
  }
}

/** Return the last completed non-daily session id for this derived game. */
export function lastDerivedReplayId(game: DerivedReplayGame): string | null {
  const memory = read();
  if (memory.migrate) write(memory.ids);
  return memory.ids[game] ?? null;
}

/** Replace this game's sole remembered id; total storage remains capped at two ids. */
export function rememberDerivedReplayId(
  game: DerivedReplayGame,
  gameId: string,
): void {
  const id = normalizeSessionId(gameId);
  if (!id) return;
  const memory = read();
  write({ ...memory.ids, [game]: id });
}
