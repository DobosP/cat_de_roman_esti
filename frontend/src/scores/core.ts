// scores/core.ts — mechanical module boundary; declarations copied from scores.ts.


export interface ScoreEntry {
  /** Numeric score, higher is better. */
  score: number;
  /** Short human summary of the run (e.g. "3 încercări", "1000 pct"). */
  detail: string;
  /** ms epoch. */
  at: number;
  /** Stable opaque key for this completed puzzle/run shape. */
  puzzleKey?: string;
  /** YYYY-MM-DD when this was a daily run. */
  daily?: string;
  /** Difficulty tier for non-daily runs. */
  difficulty?: string;
  /** Category/theme key when the run was category-scoped (ADR-0011). */
  category?: string;
}

export interface GameRecord {
  best: ScoreEntry | null;
  played: number;
  recent: ScoreEntry[]; // newest first, capped
  puzzles?: Record<string, ScoreEntry>;
  /** Legacy/export-compatible marker: at least one completed run was not a shared daily. */
  completedNonDaily: boolean;
  /** Monotonic, bounded count used by the derived-game starter progression. */
  nonDailyCompletions: number;
  /** Monotonic marker: at least one non-daily terminal score was positive. */
  nonDailyWon: boolean;
}

export type Board = Record<string, GameRecord>;

export type DerivedStarterGame = "intrusul" | "perechi";

export interface GameScoreEntry extends ScoreEntry {
  game: string;
}

export interface DailyStreakRecord {
  lastDate: string;
  length: number;
}

export const STORAGE_KEY = "cat_wordgame_scores_v1";

export const GAME_CAP = 16;

export const RECENT_CAP = 50;

export const PUZZLE_CAP = 100;

export const DERIVED_STARTER_COMPLETIONS = 3;

export const STREAK_KEY = "_streak";

export const RECEIPTS_KEY = "_completionReceipts";

export const DAILY_STREAK_CAP = 20_000;

export function loadRaw(storage = browserStorage()): Record<string, unknown> {
  if (!storage) return {};
  try {
    const parsed = JSON.parse(storage.getItem(STORAGE_KEY) || "{}");
    return isRecord(parsed) ? parsed : {};
  } catch {
    return {};
  }
}

export function load(): Board {
  return normalizeBoard(loadRaw());
}

export function save(
  board: Board,
  streak?: unknown,
  receipts?: unknown,
  storage = browserStorage(),
): boolean {
  if (!storage) return false;
  try {
    const payload: Record<string, unknown> = { ...board };
    if (streak !== undefined) payload[STREAK_KEY] = streak;
    if (receipts !== undefined) payload[RECEIPTS_KEY] = receipts;
    storage.setItem(STORAGE_KEY, JSON.stringify(payload));
    return true;
  } catch {
    /* best-effort */
    return false;
  }
}

export function browserStorage(): Pick<Storage, "getItem" | "setItem" | "removeItem"> | null {
  try {
    return typeof localStorage === "undefined" ? null : localStorage;
  } catch {
    return null;
  }
}

export function normalizeBoard(value: unknown): Board {
  if (!isRecord(value)) return {};
  const board: Board = {};
  const gameEntries = Object.entries(value)
    .filter(([key]) => key !== STREAK_KEY && key !== RECEIPTS_KEY)
    .slice(0, GAME_CAP);
  for (const [game, rawRec] of gameEntries) {
    if (!isRecord(rawRec)) continue;
    const recent = Array.isArray(rawRec.recent)
      ? rawRec.recent.map(normalizeEntry).filter((x): x is ScoreEntry => Boolean(x))
      : [];
    const puzzlesRaw = isRecord(rawRec.puzzles) ? rawRec.puzzles : {};
    const puzzles: Record<string, ScoreEntry> = {};
    for (const [key, rawEntry] of Object.entries(puzzlesRaw)) {
      const entry = normalizeEntry(rawEntry);
      if (entry && key.trim()) puzzles[key] = { ...entry, puzzleKey: key };
    }
    // A saved 0-point best (older builds recorded losses) is dropped; history keeps it.
    const stored = normalizeEntry(rawRec.best);
    const best = stored && stored.score > 0 ? stored : bestOf([...recent, ...Object.values(puzzles)]);
    // Old exports may only have `completedNonDaily`, or no progress markers at all.
    // Infer bounded progress from distinct retained normal entries. A legacy boolean
    // with no surviving entry means one unknown/lost attempt, never an assumed win.
    const retained = uniqueEntries([
      ...recent,
      ...Object.values(puzzles),
      ...(stored ? [stored] : []),
    ]);
    const retainedNonDaily = retained.filter((entry) => !entry.daily);
    const hasStoredProgress =
      isNonNegativeInteger(rawRec.nonDailyCompletions) &&
      typeof rawRec.nonDailyWon === "boolean";
    const storedCompletions = boundedStarterCompletions(
      rawRec.nonDailyCompletions,
    );
    const storedWin = rawRec.nonDailyWon === true;
    const completedNonDaily =
      rawRec.completedNonDaily === true ||
      storedCompletions > 0 ||
      storedWin ||
      retainedNonDaily.length > 0;
    const nonDailyWon = hasStoredProgress
      ? storedWin
      : retainedNonDaily.some((entry) => entry.score > 0);
    const nonDailyCompletions = hasStoredProgress
      ? Math.max(storedCompletions, nonDailyWon ? 1 : 0)
      : Math.min(
          DERIVED_STARTER_COMPLETIONS,
          Math.max(
            retainedNonDaily.length,
            completedNonDaily ? 1 : 0,
            nonDailyWon ? 1 : 0,
          ),
        );
    board[game] = {
      best,
      played: clampNumber(rawRec.played, recent.length),
      recent: recent.sort((a, b) => b.at - a.at).slice(0, RECENT_CAP),
      completedNonDaily,
      nonDailyCompletions,
      nonDailyWon,
      ...(Object.keys(puzzles).length ? { puzzles: capPuzzles(puzzles) } : {}),
    };
  }
  return board;
}

export function normalizeEntry(value: unknown): ScoreEntry | null {
  if (!isRecord(value)) return null;
  const score = clampNumber(value.score, NaN);
  const at = clampNumber(value.at, NaN);
  const detail = typeof value.detail === "string" ? value.detail.trim().slice(0, 120) : "";
  if (!Number.isFinite(score) || !Number.isFinite(at) || !detail) return null;
  return {
    score,
    detail,
    at,
    ...(typeof value.puzzleKey === "string" && value.puzzleKey.trim()
      ? { puzzleKey: value.puzzleKey.trim().slice(0, 160) }
      : {}),
    ...(typeof value.daily === "string" && value.daily.trim()
      ? { daily: value.daily.trim().slice(0, 10) }
      : {}),
    ...(typeof value.difficulty === "string" && value.difficulty.trim()
      ? { difficulty: value.difficulty.trim().slice(0, 20) }
      : {}),
    ...(typeof value.category === "string" && value.category.trim()
      ? { category: value.category.trim().slice(0, 40) }
      : {}),
  };
}

export function uniqueEntries(entries: ScoreEntry[]): ScoreEntry[] {
  const seen = new Set<string>();
  return entries.filter((entry) => {
    const key = [
      entry.at,
      entry.score,
      entry.detail,
      entry.puzzleKey ?? "",
      entry.daily ?? "",
    ].join(":");
    if (seen.has(key)) return false;
    seen.add(key);
    return true;
  });
}

export function retainedScoreEntries(value: unknown): ScoreEntry[] {
  if (!isRecord(value)) return [];
  const candidates: unknown[] = Array.isArray(value.recent) ? [...value.recent] : [];
  if (value.best !== undefined) candidates.push(value.best);
  if (isRecord(value.puzzles)) candidates.push(...Object.values(value.puzzles));
  return candidates
    .map(normalizeEntry)
    .filter((entry): entry is ScoreEntry => entry !== null);
}

export function isDailyKey(value: unknown): value is string {
  if (typeof value !== "string") return false;
  const match = /^(\d{4})-(\d{2})-(\d{2})$/.exec(value);
  if (!match) return false;
  const year = Number(match[1]);
  const month = Number(match[2]);
  const day = Number(match[3]);
  if (year < 1 || month < 1 || month > 12 || day < 1) return false;
  const leapYear = year % 4 === 0 && (year % 100 !== 0 || year % 400 === 0);
  const daysInMonth = [
    31,
    leapYear ? 29 : 28,
    31,
    30,
    31,
    30,
    31,
    31,
    30,
    31,
    30,
    31,
  ];
  return day <= daysInMonth[month - 1]!;
}

export function daysBetween(a: string, b: string): number {
  const parse = (value: string): number => {
    const match = /^(\d{4})-(\d{2})-(\d{2})$/.exec(value);
    if (!match) return NaN;
    return Date.UTC(Number(match[1]), Number(match[2]) - 1, Number(match[3]));
  };
  return Math.round((parse(b) - parse(a)) / 86_400_000);
}

export function normalizeStreak(value: unknown, board: Board): DailyStreakRecord {
  if (isRecord(value) && isNonNegativeInteger(value.length)) {
    if (value.lastDate === "" && value.length === 0) return { lastDate: "", length: 0 };
    if (isDailyKey(value.lastDate)) {
      return { lastDate: value.lastDate, length: Math.min(DAILY_STREAK_CAP, value.length) };
    }
  }
  return recomputeStreakFromBoard(board);
}

export function recomputeStreakFromBoard(board: Board): DailyStreakRecord {
  const days = new Set<string>();
  for (const record of Object.values(board)) {
    for (const entry of retainedScoreEntries(record)) {
      if (entry.daily && isDailyKey(entry.daily)) days.add(entry.daily);
    }
  }
  if (days.size === 0) return { lastDate: "", length: 0 };
  const sorted = [...days].sort();
  const mostRecent = sorted[sorted.length - 1]!;
  let length = 1;
  let cursor = mostRecent;
  for (let i = sorted.length - 2; i >= 0; i -= 1) {
    const candidate = sorted[i]!;
    if (daysBetween(candidate, cursor) !== 1) break;
    length += 1;
    cursor = candidate;
  }
  return { lastDate: mostRecent, length };
}

export function advanceStreak(current: DailyStreakRecord, day: string): DailyStreakRecord {
  if (!current.lastDate) return { lastDate: day, length: 1 };
  const gap = daysBetween(current.lastDate, day);
  if (gap === 0) return current;
  if (gap === 1) return { lastDate: day, length: Math.min(DAILY_STREAK_CAP, current.length + 1) };
  if (gap < 0) return current;
  return { lastDate: day, length: 1 };
}

export function boundedStarterCompletions(value: unknown): number {
  if (!isNonNegativeInteger(value)) return 0;
  return Math.min(DERIVED_STARTER_COMPLETIONS, value);
}

export function isNonNegativeInteger(value: unknown): value is number {
  return typeof value === "number" && Number.isInteger(value) && value >= 0;
}

export function bestOf(entries: Array<ScoreEntry | null | undefined>): ScoreEntry | null {
  return entries
    .filter((x): x is ScoreEntry => Boolean(x && x.score > 0))
    .sort((a, b) => b.score - a.score || b.at - a.at)[0] ?? null;
}

export function capPuzzles(puzzles: Record<string, ScoreEntry>): Record<string, ScoreEntry> {
  return Object.fromEntries(
    Object.entries(puzzles)
      .sort((a, b) => b[1].at - a[1].at)
      .slice(0, PUZZLE_CAP),
  );
}

export function clampNumber(value: unknown, fallback: number): number {
  const n = typeof value === "number" ? value : Number(value);
  return Number.isFinite(n) ? n : fallback;
}

export function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}
