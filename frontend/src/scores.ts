// Public compatibility facade for the offline score store.
// Production consumers use the narrow modules; the facade retains every original export.
export type { ScoreEntry, GameRecord, Board, DerivedStarterGame, GameScoreEntry } from "./scores/core";
export type { RecordOutcome, RecordScoreOptions } from "./scores/record";
export { recordScoreCompletionOnce, recordScore } from "./scores/record";
export { bestScore, timesPlayed, bestPuzzleScore, scoreBoard, recentScores, dailyScores, leaderboard } from "./scores/read";
export type { DailyCircuitGame, DailyCircuitRow, DailyCircuitSummary } from "./scores/daily";
export { DAILY_CIRCUIT_GAME_KEYS, needsDerivedStarter, getDailyStreak, buildDailyCircuit } from "./scores/daily";
export type { ImportOutcome } from "./scores/history";
export { exportScores, importScores, clearScores } from "./scores/history";
