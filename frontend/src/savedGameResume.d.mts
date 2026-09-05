export type ResumeTerminalPolicy = "adopt" | "discard";
export type ResumeTransientPolicy = "forget" | "retain";

export type ResumeOutcome<T> =
  | { kind: "none" }
  | { kind: "resumed"; gameId: string; state: T; terminal: boolean }
  | { kind: "terminal-discarded"; gameId: string; state: T }
  | { kind: "missing"; gameId: string; error: unknown }
  | { kind: "failed"; gameId: string; error: unknown };

export interface SavedGamePointer {
  peek: () => string | null;
  forget: () => void;
}

export interface SavedGameResumeAttempt<T> {
  hasSavedGame: boolean;
  runOnce: () => Promise<ResumeOutcome<T>>;
}

export function createSavedGameResume<T>(options: {
  active: SavedGamePointer;
  load: (gameId: string) => Promise<T>;
  isTerminal: (state: T) => boolean;
  terminal: ResumeTerminalPolicy;
  transient: ResumeTransientPolicy;
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
  },
): () => void;
