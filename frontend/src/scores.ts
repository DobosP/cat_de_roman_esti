// scores.ts — an OFFLINE local history store (localStorage), shared by every word game.
// No accounts, no server: each game records score metadata that was already visible at
// result time. Degrades to a no-op when storage is unavailable (private mode) — never throws.

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

const STORAGE_KEY = "cat_wordgame_scores_v1";
const EXPORT_SCHEMA = "cat-wordgame-history-v2";
const GAME_CAP = 16;
const RECENT_CAP = 50;
const PUZZLE_CAP = 100;
const DERIVED_STARTER_COMPLETIONS = 3;

export type Board = Record<string, GameRecord>;
export type DerivedStarterGame = "intrusul" | "perechi";

export interface GameScoreEntry extends ScoreEntry {
  game: string;
}

function load(): Board {
  if (typeof localStorage === "undefined") return {};
  try {
    return normalizeBoard(JSON.parse(localStorage.getItem(STORAGE_KEY) || "{}"));
  } catch {
    return {};
  }
}

function save(board: Board): void {
  if (typeof localStorage === "undefined") return;
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(board));
  } catch {
    /* best-effort */
  }
}

export interface RecordOutcome {
  isBest: boolean;
  isPuzzleBest: boolean;
  prev: ScoreEntry | null;
  prevPuzzle: ScoreEntry | null;
}

export interface RecordScoreOptions {
  /** Stable, deterministic key for this exact completed puzzle/run shape. */
  puzzleKey?: string | null;
  /** Difficulty tier for history filtering. */
  difficulty?: string | null;
  /** YYYY-MM-DD for daily history filtering. */
  daily?: string | null;
  /** Category/theme key for category-scoped runs. */
  category?: string | null;
}

/** Record a finished game for `game`. New best = strictly higher score. */
export function recordScore(
  game: string,
  score: number,
  detail: string,
  options: RecordScoreOptions = {},
): RecordOutcome {
  const board = load();
  const rec: GameRecord = board[game] ?? {
    best: null,
    played: 0,
    recent: [],
    completedNonDaily: false,
    nonDailyCompletions: 0,
    nonDailyWon: false,
  };
  const prev = rec.best;
  const puzzleKey = options.puzzleKey?.trim() || null;
  const entry = normalizeEntry({
    score,
    detail,
    at: Date.now(),
    puzzleKey: puzzleKey ?? undefined,
    difficulty: options.difficulty?.trim() || undefined,
    daily: options.daily?.trim() || undefined,
    category: options.category?.trim() || undefined,
  });
  if (!entry) return { isBest: false, isPuzzleBest: false, prev, prevPuzzle: null };
  const isBest = prev === null || score > prev.score;
  const prevPuzzle = puzzleKey ? (rec.puzzles?.[puzzleKey] ?? null) : null;
  const isPuzzleBest = puzzleKey !== null && (prevPuzzle === null || score > prevPuzzle.score);
  rec.played += 1;
  rec.recent = [entry, ...rec.recent].slice(0, RECENT_CAP);
  if (!entry.daily) {
    rec.completedNonDaily = true;
    rec.nonDailyCompletions = Math.min(
      DERIVED_STARTER_COMPLETIONS,
      rec.nonDailyCompletions + 1,
    );
    if (entry.score > 0) rec.nonDailyWon = true;
  }
  if (isBest) rec.best = entry;
  if (puzzleKey && isPuzzleBest) {
    rec.puzzles = { ...(rec.puzzles ?? {}), [puzzleKey]: entry };
    rec.puzzles = capPuzzles(rec.puzzles);
  }
  board[game] = rec;
  save(board);
  return { isBest, isPuzzleBest, prev, prevPuzzle };
}

export function bestScore(game: string): ScoreEntry | null {
  return load()[game]?.best ?? null;
}

export function timesPlayed(game: string): number {
  return load()[game]?.played ?? 0;
}

/** Keep a derived game on its starter shelf until mastery or three normal attempts. */
export function needsDerivedStarter(game: DerivedStarterGame): boolean {
  const record = load()[game];
  return (
    !record ||
    (!record.nonDailyWon &&
      record.nonDailyCompletions < DERIVED_STARTER_COMPLETIONS)
  );
}

export function bestPuzzleScore(game: string, puzzleKey: string | null | undefined): ScoreEntry | null {
  if (!puzzleKey) return null;
  return load()[game]?.puzzles?.[puzzleKey] ?? null;
}

export function scoreBoard(): Board {
  return load();
}

export function recentScores(game?: string, limit = 30): GameScoreEntry[] {
  const board = load();
  const rows = Object.entries(board).flatMap(([key, rec]) =>
    rec.recent.map((entry) => ({ ...entry, game: key })),
  );
  return rows
    .filter((entry) => !game || entry.game === game)
    .sort((a, b) => b.at - a.at)
    .slice(0, Math.max(0, limit));
}

export function dailyScores(day: string, limit = 30): GameScoreEntry[] {
  return recentScores(undefined, RECENT_CAP * 8)
    .filter((entry) => entry.daily === day)
    .slice(0, Math.max(0, limit));
}

export function leaderboard(limit = 12): GameScoreEntry[] {
  return Object.entries(load())
    .flatMap(([game, rec]) => (rec.best ? [{ ...rec.best, game }] : []))
    .sort((a, b) => b.score - a.score || b.at - a.at)
    .slice(0, Math.max(0, limit));
}

export function exportScores(): string {
  return JSON.stringify(
    {
      schema: EXPORT_SCHEMA,
      exportedAt: new Date().toISOString(),
      games: load(),
    },
    null,
    2,
  );
}

export interface ImportOutcome {
  games: number;
  entries: number;
}

export function importScores(raw: string): ImportOutcome {
  let parsed: unknown;
  try {
    parsed = JSON.parse(raw);
  } catch {
    throw new Error("Fisierul nu este JSON valid.");
  }

  const incoming = normalizeBoard(
    isRecord(parsed) && isRecord(parsed.games) ? parsed.games : parsed,
  );
  const current = load();
  let entries = 0;

  for (const [game, rec] of Object.entries(incoming)) {
    const base: GameRecord = current[game] ?? {
      best: null,
      played: 0,
      recent: [],
      completedNonDaily: false,
      nonDailyCompletions: 0,
      nonDailyWon: false,
    };
    const recent = mergeEntries(base.recent, rec.recent);
    entries += rec.recent.length;
    const puzzles = mergePuzzles(base.puzzles ?? {}, rec.puzzles ?? {});
    const best = bestOf([base.best, rec.best, ...recent, ...Object.values(puzzles)]);
    current[game] = {
      best,
      played: Math.max(base.played, rec.played, recent.length),
      recent,
      completedNonDaily: base.completedNonDaily || rec.completedNonDaily,
      nonDailyCompletions: Math.min(
        DERIVED_STARTER_COMPLETIONS,
        Math.max(base.nonDailyCompletions, rec.nonDailyCompletions),
      ),
      nonDailyWon: base.nonDailyWon || rec.nonDailyWon,
      ...(Object.keys(puzzles).length ? { puzzles } : {}),
    };
  }

  save(current);
  return { games: Object.keys(incoming).length, entries };
}

export function clearScores(): void {
  save({});
}

function normalizeBoard(value: unknown): Board {
  if (!isRecord(value)) return {};
  const board: Board = {};
  for (const [game, rawRec] of Object.entries(value).slice(0, GAME_CAP)) {
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
    const best = normalizeEntry(rawRec.best) ?? bestOf([...recent, ...Object.values(puzzles)]);
    // Old exports may only have `completedNonDaily`, or no progress markers at all.
    // Infer bounded progress from distinct retained normal entries. A legacy boolean
    // with no surviving entry means one unknown/lost attempt, never an assumed win.
    const retained = uniqueEntries([
      ...recent,
      ...Object.values(puzzles),
      ...(best ? [best] : []),
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

function normalizeEntry(value: unknown): ScoreEntry | null {
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

function mergeEntries(a: ScoreEntry[], b: ScoreEntry[]): ScoreEntry[] {
  const seen = new Set<string>();
  return [...a, ...b]
    .sort((x, y) => y.at - x.at)
    .filter((entry) => {
      const key = `${entry.at}:${entry.score}:${entry.detail}:${entry.puzzleKey ?? ""}`;
      if (seen.has(key)) return false;
      seen.add(key);
      return true;
    })
    .slice(0, RECENT_CAP);
}

function uniqueEntries(entries: ScoreEntry[]): ScoreEntry[] {
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

function boundedStarterCompletions(value: unknown): number {
  if (!isNonNegativeInteger(value)) return 0;
  return Math.min(DERIVED_STARTER_COMPLETIONS, value);
}

function isNonNegativeInteger(value: unknown): value is number {
  return typeof value === "number" && Number.isInteger(value) && value >= 0;
}

function bestOf(entries: Array<ScoreEntry | null | undefined>): ScoreEntry | null {
  return entries
    .filter((x): x is ScoreEntry => Boolean(x))
    .sort((a, b) => b.score - a.score || b.at - a.at)[0] ?? null;
}

function capPuzzles(puzzles: Record<string, ScoreEntry>): Record<string, ScoreEntry> {
  return Object.fromEntries(
    Object.entries(puzzles)
      .sort((a, b) => b[1].at - a[1].at)
      .slice(0, PUZZLE_CAP),
  );
}

function mergePuzzles(
  a: Record<string, ScoreEntry>,
  b: Record<string, ScoreEntry>,
): Record<string, ScoreEntry> {
  const merged: Record<string, ScoreEntry> = { ...a };
  for (const [key, entry] of Object.entries(b)) {
    const current = merged[key];
    if (!current || entry.score > current.score || (entry.score === current.score && entry.at > current.at)) {
      merged[key] = entry;
    }
  }
  return capPuzzles(merged);
}

function clampNumber(value: unknown, fallback: number): number {
  const n = typeof value === "number" ? value : Number(value);
  return Number.isFinite(n) ? n : fallback;
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}
