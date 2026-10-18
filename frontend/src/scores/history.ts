// scores/history.ts — mechanical module boundary; declarations copied from scores.ts.

import type { GameRecord, ScoreEntry } from "./core";
import { load, loadRaw, normalizeBoard, normalizeStreak, save, isRecord, bestOf, capPuzzles, RECENT_CAP, DERIVED_STARTER_COMPLETIONS, STREAK_KEY, RECEIPTS_KEY } from "./core";

const EXPORT_SCHEMA = "cat-wordgame-history-v2";

export interface ImportOutcome {
  games: number;
  entries: number;
}

const INVALID_IMPORT_MESSAGE = "Fișierul ales nu este un export de istoric valid.";

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

export function importScores(raw: string): ImportOutcome {
  let parsed: unknown;
  try {
    parsed = JSON.parse(raw);
  } catch {
    throw new Error(INVALID_IMPORT_MESSAGE);
  }

  const incoming = normalizeBoard(
    isRecord(parsed) && isRecord(parsed.games) ? parsed.games : parsed,
  );
  // Valid JSON of the wrong shape must not report "Importat: 0 rezultate în 0 jocuri."
  if (Object.keys(incoming).length === 0) throw new Error(INVALID_IMPORT_MESSAGE);
  const existingRaw = loadRaw();
  const current = normalizeBoard(existingRaw);
  // Snapshot the local streak before merging. If this device has legacy daily rows but
  // no explicit streak record, normalize them now; imported rows must never create one.
  const localStreak = normalizeStreak(existingRaw[STREAK_KEY], current);
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

  // The daily streak is local-device state, not imported/exported history.
  save(current, localStreak, existingRaw[RECEIPTS_KEY]);
  return { games: Object.keys(incoming).length, entries };
}

export function clearScores(): void {
  save({});
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
