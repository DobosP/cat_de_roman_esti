// scores.ts — a tiny OFFLINE per-game personal-best store (localStorage), shared by every
// word game. No accounts, no server: each game records a numeric score (higher = better)
// plus a short human detail (e.g. "4 mutari"); we keep the best and a small recent history.
// Degrades to a no-op when storage is unavailable (private mode) — never throws.

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
  prev: ScoreEntry | null;
}

/** Record a finished game for `game`. New best = strictly higher score. */
export function recordScore(game: string, score: number, detail: string): RecordOutcome {
  const board = load();
  const rec: GameRecord = board[game] ?? { best: null, played: 0, recent: [] };
  const prev = rec.best;
  const entry: ScoreEntry = { score, detail, at: Date.now() };
  const isBest = prev === null || score > prev.score;
  rec.played += 1;
  rec.recent = [entry, ...rec.recent].slice(0, RECENT_CAP);
  if (isBest) rec.best = entry;
  board[game] = rec;
  save(board);
  return { isBest, prev };
}

export function bestScore(game: string): ScoreEntry | null {
  return load()[game]?.best ?? null;
}

export function timesPlayed(game: string): number {
  return load()[game]?.played ?? 0;
}
