// scoreSync.ts — best-effort mirror of the local score history to the logged-in account.
//
// The browser localStorage store (scores.ts) stays the source of truth for offline play;
// when the user is signed in AND has completed consent, finished runs are also pushed to
// the server (idempotent — the backend dedups on user+game+at+puzzle_key). Never throws:
// a failed sync must not break gameplay.

import { postAuth } from "./api/auth";
import { recentScores, scoreBoard, type GameScoreEntry } from "./scores";

let enabled = false;
let didFullSync = false;

export function setScoreSyncEnabled(on: boolean): void {
  enabled = on;
  if (!on) didFullSync = false;
}

function toServer(entry: GameScoreEntry) {
  return {
    game: entry.game,
    score: entry.score,
    detail: entry.detail,
    at: entry.at,
    puzzle_key: entry.puzzleKey ?? "",
    daily: entry.daily ?? "",
    difficulty: entry.difficulty ?? "",
    category: entry.category ?? "",
  };
}

/** Push the single most-recent run for `game` (called right after it is recorded). */
export async function pushLatest(game: string): Promise<void> {
  if (!enabled) return;
  const latest = recentScores(game, 1)[0];
  if (!latest) return;
  try {
    await postAuth("/api/me/scores", { entries: [toServer(latest)] });
  } catch {
    /* best-effort: offline localStorage remains the source of truth */
  }
}

/** One-shot upload of the whole local board when a session first becomes save-capable. */
export async function syncAllLocalOnce(): Promise<void> {
  if (!enabled || didFullSync) return;
  didFullSync = true;
  const board = scoreBoard();
  const entries = Object.entries(board)
    .flatMap(([game, rec]) => rec.recent.map((e) => toServer({ ...e, game })))
    .slice(0, 500);
  if (!entries.length) return;
  try {
    await postAuth("/api/me/scores", { entries });
  } catch {
    didFullSync = false; // allow a later retry
  }
}
