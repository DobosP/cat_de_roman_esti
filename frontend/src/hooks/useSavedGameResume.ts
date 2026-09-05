import { useEffect, useMemo } from "react";
import { ApiError } from "../api/client";
import type { ActiveGameMemo } from "./useActiveGame";
import {
  createSavedGameResume,
  subscribeSavedGameResume,
  type ResumeTerminalPolicy,
  type ResumeTransientPolicy,
} from "../savedGameResume.mjs";

interface SavedGameResumeOptions<T> {
  active: ActiveGameMemo;
  load: (gameId: string) => Promise<T>;
  isTerminal: (state: T) => boolean;
  terminal: ResumeTerminalPolicy;
  transient: ResumeTransientPolicy;
  setPending: (pending: boolean) => void;
  onResume: (state: T) => void;
  onTransientError?: (error: unknown) => void;
}

/** Resume one saved server session without owning any game-specific screen state. */
export function useSavedGameResume<T>({
  active,
  load,
  isTerminal,
  terminal,
  transient,
  setPending,
  onResume,
  onTransientError,
}: SavedGameResumeOptions<T>): void {
  const attempt = useMemo(
    () =>
      createSavedGameResume({
        active,
        load,
        isTerminal,
        terminal,
        transient,
        isMissing: (error) => error instanceof ApiError && error.status === 404,
      }),
    [active, isTerminal, load, terminal, transient],
  );

  useEffect(
    () =>
      subscribeSavedGameResume(attempt, {
        setPending,
        onResume,
        onTransientError,
      }),
    [attempt, onResume, onTransientError, setPending],
  );
}
