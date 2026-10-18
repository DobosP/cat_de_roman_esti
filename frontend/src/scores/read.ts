// scores/read.ts — mechanical module boundary; declarations copied from scores.ts.

import type { Board, ScoreEntry, GameScoreEntry } from "./core";
import { load, RECENT_CAP } from "./core";

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
