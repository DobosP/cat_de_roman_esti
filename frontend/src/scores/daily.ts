// scores/daily.ts — mechanical module boundary; declarations copied from scores.ts.

import type { DerivedStarterGame } from "./core";
import { load, loadRaw, normalizeStreak, normalizeBoard, isDailyKey, daysBetween, isRecord, retainedScoreEntries, DERIVED_STARTER_COMPLETIONS, STREAK_KEY } from "./core";

export const DAILY_CIRCUIT_GAME_KEYS = Object.freeze(
  [
    "alchimie",
    "intrusul",
    "perechi",
    "conexiuni",
    "contexto",
    "lant",
  ] as const,
);

export type DailyCircuitGame = (typeof DAILY_CIRCUIT_GAME_KEYS)[number];

export interface DailyCircuitRow {
  game: DailyCircuitGame;
  completed: boolean;
  score: number;
}

export interface DailyCircuitSummary {
  day: string;
  completed: number;
  total: number;
  games: DailyCircuitRow[];
}

const DAILY_CIRCUIT_SCORE_CAP = 1_000;

export function needsDerivedStarter(game: DerivedStarterGame): boolean {
  const record = load()[game];
  return (
    !record ||
    (!record.nonDailyWon &&
      record.nonDailyCompletions < DERIVED_STARTER_COMPLETIONS)
  );
}

export function getDailyStreak(today: string): number {
  const raw = loadRaw();
  const streak = normalizeStreak(raw[STREAK_KEY], normalizeBoard(raw));
  if (!streak.lastDate || !isDailyKey(today)) return 0;
  const gap = daysBetween(streak.lastDate, today);
  if (!Number.isFinite(gap) || gap < 0 || gap > 1) return 0;
  return streak.length;
}

export function buildDailyCircuit(board: unknown, day: string): DailyCircuitSummary {
  const source = isRecord(board) ? board : {};
  const daily = isDailyKey(day) ? day : "";
  const games = DAILY_CIRCUIT_GAME_KEYS.map((game): DailyCircuitRow => {
    const matching = daily
      ? retainedScoreEntries(source[game]).filter((entry) => entry.daily === daily)
      : [];
    const completed = matching.length > 0;
    const score = completed
      ? matching.reduce(
          (best, entry) => Math.max(best, clampDailyCircuitScore(entry.score)),
          0,
        )
      : 0;
    return { game, completed, score };
  });

  return {
    day: daily,
    completed: games.filter((game) => game.completed).length,
    total: Math.min(
      DAILY_CIRCUIT_SCORE_CAP * DAILY_CIRCUIT_GAME_KEYS.length,
      games.reduce((sum, game) => sum + game.score, 0),
    ),
    games,
  };
}

function clampDailyCircuitScore(score: number): number {
  return Math.min(DAILY_CIRCUIT_SCORE_CAP, Math.max(0, score));
}
