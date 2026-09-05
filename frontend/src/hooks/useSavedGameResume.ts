import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { ApiError } from "../api/client";
import type { ActiveGameMemo } from "./useActiveGame";
import {
  createSavedGameResume,
  subscribeSavedGameResume,
} from "../savedGameResume.mjs";

export type ResumeRecovery =
  | { kind: "failed" }
  | { kind: "changed"; hasCurrent: boolean };

export interface SavedGameResumeControl {
  recovery: ResumeRecovery | null;
  retryResume: () => void;
  cancelResume: () => void;
}

interface SavedGameResumeOptions<T> {
  active: ActiveGameMemo;
  load: (gameId: string) => Promise<T>;
  isTerminal: (state: T) => boolean;
  setPending: (pending: boolean) => void;
  onResume: (state: T, detail: { gameId: string; terminal: boolean }) => void;
}

/** Resume one saved server session without owning any game-specific screen state. */
export function useSavedGameResume<T>({
  active,
  load,
  isTerminal,
  setPending,
  onResume,
}: SavedGameResumeOptions<T>): SavedGameResumeControl {
  const [generation, setGeneration] = useState(0);
  const [recovery, setRecovery] = useState<ResumeRecovery | null>(null);
  const unsubscribeRef = useRef<(() => void) | null>(null);
  const attempt = useMemo(
    () =>
      createSavedGameResume({
        active,
        load,
        isTerminal,
        isMissing: (error) => error instanceof ApiError && error.status === 404,
      }),
    // generation deliberately creates a fresh snapshot of the current saved pointer.
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [active, generation, isTerminal, load],
  );

  useEffect(() => {
    const unsubscribe = subscribeSavedGameResume(attempt, {
        setPending,
        onResume: (state, detail) => {
          setRecovery(null);
          onResume(state, detail);
        },
        onTransientError: () => setRecovery({ kind: "failed" }),
        onSuperseded: (hasCurrent) => setRecovery({ kind: "changed", hasCurrent }),
      });
    unsubscribeRef.current = unsubscribe;
    return () => {
      unsubscribe();
      if (unsubscribeRef.current === unsubscribe) unsubscribeRef.current = null;
    };
  }, [attempt, onResume, setPending]);

  const retryResume = useCallback(() => {
    unsubscribeRef.current?.();
    setRecovery(null);
    setGeneration((value) => value + 1);
  }, []);

  const cancelResume = useCallback(() => {
    unsubscribeRef.current?.();
    setRecovery(null);
  }, []);

  return { recovery, retryResume, cancelResume };
}
