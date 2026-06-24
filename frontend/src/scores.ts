// scores.ts — a tiny OFFLINE personal-best store (localStorage), shared by every word game.
// No accounts, no server: each game records a numeric score (higher = better), a short
// human detail, a small recent history, and optional per-puzzle bests. Degrades to a
// no-op when storage is unavailable (private mode) — never throws.

export interface ScoreEntry {
  /** Numeric score, higher is better. */
  score: number;
  /** Short human summary of the run (e.g. "3 incercari", "1000 pct"). */
  detail: string;
  /** ms epoch. */
  at: number;
}

interface GameRecord {
  best: ScoreEntry | null;
  played: number;
  recent: ScoreEntry[]; // newest first, capped
  puzzles?: Record<string, ScoreEntry>;
}

const STORAGE_KEY = "cat_wordgame_scores_v1";
const RECENT_CAP = 10;

type Board = Record<string, GameRecord>;

function load(): Board {
  if (typeof localStorage === "undefined") return {};
  try {
    return (JSON.parse(localStorage.getItem(STORAGE_KEY) || "{}") as Board) ?? {};
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
}

/** Record a finished game for `game`. New best = strictly higher score. */
export function recordScore(
  game: string,
  score: number,
  detail: string,
  options: RecordScoreOptions = {},
): RecordOutcome {
  const board = load();
  const rec: GameRecord = board[game] ?? { best: null, played: 0, recent: [] };
  const prev = rec.best;
  const entry: ScoreEntry = { score, detail, at: Date.now() };
  const isBest = prev === null || score > prev.score;
  const puzzleKey = options.puzzleKey?.trim() || null;
  const prevPuzzle = puzzleKey ? (rec.puzzles?.[puzzleKey] ?? null) : null;
  const isPuzzleBest = puzzleKey !== null && (prevPuzzle === null || score > prevPuzzle.score);
  rec.played += 1;
  rec.recent = [entry, ...rec.recent].slice(0, RECENT_CAP);
  if (isBest) rec.best = entry;
  if (puzzleKey && isPuzzleBest) {
    rec.puzzles = { ...(rec.puzzles ?? {}), [puzzleKey]: entry };
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

export function bestPuzzleScore(game: string, puzzleKey: string | null | undefined): ScoreEntry | null {
  if (!puzzleKey) return null;
  return load()[game]?.puzzles?.[puzzleKey] ?? null;
}
