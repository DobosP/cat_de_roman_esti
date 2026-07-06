// useRecordScore — the one guard for "record this finished game exactly once".
// Every screen previously rolled its own (ref / state / nothing), which let a
// re-render double-record a result; this hook keys the guard on the server's
// game id so replays record again but re-renders never do.

import { useCallback, useRef } from "react";
import { recordScore, type RecordOutcome, type RecordScoreOptions } from "../scores";

export type RecordOnce = (
  gameId: string,
  score: number,
  detail: string,
  options?: RecordScoreOptions,
) => RecordOutcome | null;

export function useRecordScore(game: string): RecordOnce {
  const recorded = useRef<string | null>(null);
  return useCallback(
    (gameId, score, detail, options) => {
      if (!gameId || recorded.current === gameId) return null;
      recorded.current = gameId;
      return recordScore(game, score, detail, options);
    },
    [game],
  );
}
