// leaderboard.ts — a tiny OFFLINE, asset-free personal-best store (localStorage).
//
// The game is offline-first and the BFF is stateless, so high scores live in the
// browser. We track, per (category, mode): the best score and the fewest hops (the
// tie-breaker among perfect 1000s), plus a single "best run" across a multi-puzzle
// session (most puzzles solved / highest cumulative score). Everything degrades to a
// no-op when storage is unavailable (private mode) — it never throws.

import type { Mode } from "./api/types";

const STORAGE_KEY = "cat_leaderboard_v1";

/** Best winning result recorded for one category+mode. */
export interface BestEntry {
  /** Highest score (0..1000). */
  score: number;
  /** Fewest hops on a winning game (tie-breaker among equal scores). */
  hops: number;
  /** Par of the recorded best game (for "X/par Y" context). */
  par: number;
  /** When it was set (ms epoch). */
  at: number;
}

/** Best multi-puzzle run (a session of consecutive solves). */
export interface RunBest {
  solved: number;
  total: number;
}

interface Board {
  best: Record<string, BestEntry>;
  run: RunBest;
}

const EMPTY: Board = { best: {}, run: { solved: 0, total: 0 } };

function key(category: string, mode: Mode): string {
  return `${category}:${mode}`;
}

function load(): Board {
  if (typeof localStorage === "undefined") return structuredCloneSafe(EMPTY);
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return structuredCloneSafe(EMPTY);
    const parsed = JSON.parse(raw) as Partial<Board>;
    return {
      best: parsed.best ?? {},
      run: parsed.run ?? { solved: 0, total: 0 },
    };
  } catch {
    return structuredCloneSafe(EMPTY);
  }
}

function save(board: Board): void {
  if (typeof localStorage === "undefined") return;
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(board));
  } catch {
    /* storage full / unavailable — best-effort only */
  }
}

// structuredClone isn't guaranteed in every target; a JSON round-trip is plenty here.
function structuredCloneSafe<T>(v: T): T {
  return JSON.parse(JSON.stringify(v)) as T;
}

/** The recorded best for a category+mode, or null if none yet. */
export function bestFor(category: string, mode: Mode): BestEntry | null {
  return load().best[key(category, mode)] ?? null;
}

export interface RecordOutcome {
  /** True when this result set a new personal best (higher score, or equal score in fewer hops). */
  isNewBest: boolean;
  /** The previous best (null if this is the first recorded game for the bucket). */
  prev: BestEntry | null;
}

/**
 * Record a WON game's result for (category, mode). A new best is a strictly higher
 * score, or an equal score reached in strictly fewer hops. Returns whether it was a
 * record and the previous best (for "you beat X" messaging).
 */
export function recordResult(
  category: string,
  mode: Mode,
  result: { score: number; hops: number; par: number },
): RecordOutcome {
  const board = load();
  const k = key(category, mode);
  const prev = board.best[k] ?? null;
  const isNewBest =
    prev === null ||
    result.score > prev.score ||
    (result.score === prev.score && result.hops < prev.hops);
  if (isNewBest) {
    board.best[k] = {
      score: result.score,
      hops: result.hops,
      par: result.par,
      at: Date.now(),
    };
    save(board);
  }
  return { isNewBest, prev };
}

/** Record a finished run; returns whether it set a new best run (by total score). */
export function recordRun(solved: number, total: number): { isNewRun: boolean } {
  if (solved <= 0) return { isNewRun: false };
  const board = load();
  const isNewRun = total > board.run.total;
  if (isNewRun) {
    board.run = { solved, total };
    save(board);
  }
  return { isNewRun };
}

export function bestRun(): RunBest {
  return load().run;
}

/** All recorded per-bucket bests, newest-strongest first — for a leaderboard panel. */
export function allBests(): Array<{ category: string; mode: Mode } & BestEntry> {
  const board = load();
  return Object.entries(board.best)
    .map(([k, v]) => {
      const [category, mode] = k.split(":");
      return { category, mode: mode as Mode, ...v };
    })
    .sort((a, b) => b.score - a.score || a.hops - b.hops);
}
