export type ResumeOutcome<T> =
  | { kind: "none" }
  | { kind: "resumed"; gameId: string; state: T; terminal: boolean }
  | { kind: "missing"; gameId: string; error: unknown }
  | { kind: "failed"; gameId: string; error: unknown }
  | { kind: "superseded"; gameId: string };

export interface SavedGamePointer {
  peek: () => string | null;
  isCurrent: (gameId: string) => boolean;
  forgetIfCurrent: (gameId: string) => boolean;
}

export interface SavedGameResumeAttempt<T> {
  hasSavedGame: boolean;
  isCurrent: () => boolean;
  hasCurrent: () => boolean;
  runOnce: () => Promise<ResumeOutcome<T>>;
}

export function createSavedGameResume<T>(options: {
  active: SavedGamePointer;
  load: (gameId: string) => Promise<T>;
  isTerminal: (state: T) => boolean;
  isMissing: (error: unknown) => boolean;
}): SavedGameResumeAttempt<T>;

export function subscribeSavedGameResume<T>(
  attempt: SavedGameResumeAttempt<T>,
  handlers: {
    setPending: (pending: boolean) => void;
    onResume: (
      state: T,
      detail: { gameId: string; terminal: boolean },
    ) => void;
    onTransientError?: (error: unknown) => void;
    onSuperseded?: (hasCurrent: boolean) => void;
  },
): () => void;
