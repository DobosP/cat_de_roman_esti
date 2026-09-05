// useRecordScore — the one guard for "record this finished game exactly once".
// Every screen previously rolled its own (ref / state / nothing), which let a
// re-render double-record a result; this hook keys the guard on the server's
// game id so replays record again but re-renders never do.

import { useCallback, useRef } from "react";
import {
  recordScoreCompletionOnce,
  type RecordOutcome,
  type RecordScoreOptions,
} from "../scores";
import { pushLatest } from "../scoreSync";

export type RecordOnce = (
  gameId: string,
  score: number,
  detail: string,
  options?: RecordScoreOptions,
) => Promise<RecordOutcome | null>;

export function useRecordScore(game: string): RecordOnce {
  const recorded = useRef<{
    gameId: string;
    outcome: Promise<RecordOutcome | null>;
  } | null>(null);
  return useCallback(
    (gameId, score, detail, options) => {
      if (!gameId) return Promise.resolve(null);
      if (recorded.current?.gameId === gameId) return recorded.current.outcome;
      const outcome = recordScoreCompletionOnce(game, gameId, score, detail, options)
        .then((fresh) => {
          // Mirror only a newly recorded row to the account when signed in + consented.
          if (fresh) void pushLatest(game);
          return fresh;
        })
        .catch(() => null);
      // StrictMode's effect teardown/setup receives the same completion promise. Keeping only
      // the current game bounds the ref across arbitrarily many replays.
      recorded.current = { gameId, outcome };
      return outcome;
    },
    [game],
  );
}
