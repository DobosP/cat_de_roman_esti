// Framework-free saved-game resume lifecycle. React uses the subscription wrapper
// below so StrictMode can unsubscribe and immediately resubscribe to the same
// single-flight request, while a real unmount receives no late callbacks.

/**
 * @template T
 * @param {{
 *   active: {peek: () => string | null, isCurrent: (gameId: string) => boolean, forgetIfCurrent: (gameId: string) => boolean},
 *   load: (gameId: string) => Promise<T>,
 *   isTerminal: (state: T) => boolean,
 *   isMissing: (error: unknown) => boolean,
 * }} options
 */
export function createSavedGameResume(options) {
  const savedId = options.active.peek();
  /** @type {Promise<import("./savedGameResume.mjs").ResumeOutcome<T>> | null} */
  let inFlight = null;

  const run = async () => {
    if (!savedId) return { kind: "none" };

    try {
      const state = await options.load(savedId);
      if (!options.active.isCurrent(savedId)) {
        return { kind: "superseded", gameId: savedId };
      }
      const terminal = options.isTerminal(state);
      return { kind: "resumed", gameId: savedId, state, terminal };
    } catch (error) {
      if (!options.active.isCurrent(savedId)) {
        return { kind: "superseded", gameId: savedId };
      }
      if (options.isMissing(error)) {
        if (!options.active.forgetIfCurrent(savedId)) {
          return { kind: "superseded", gameId: savedId };
        }
        return { kind: "missing", gameId: savedId, error };
      }
      return { kind: "failed", gameId: savedId, error };
    }
  };

  return {
    hasSavedGame: savedId !== null && savedId !== "",
    isCurrent() {
      return savedId !== null && savedId !== "" && options.active.isCurrent(savedId);
    },
    hasCurrent() {
      const current = options.active.peek();
      return current !== null && current !== "";
    },
    runOnce() {
      inFlight ??= run();
      return inFlight;
    },
  };
}

/**
 * @template T
 * @param {{hasSavedGame: boolean, runOnce: () => Promise<import("./savedGameResume.mjs").ResumeOutcome<T>>}} attempt
 * @param {{
 *   setPending: (pending: boolean) => void,
 *   onResume: (state: T, detail: {gameId: string, terminal: boolean}) => void,
 *   onTransientError?: (error: unknown) => void,
 *   onSuperseded?: (hasCurrent: boolean) => void,
 * }} handlers
 */
export function subscribeSavedGameResume(attempt, handlers) {
  let subscribed = true;
  handlers.setPending(attempt.hasSavedGame);

  if (!attempt.hasSavedGame) {
    void attempt.runOnce();
    return () => {
      subscribed = false;
    };
  }

  void attempt.runOnce().then((outcome) => {
    if (!subscribed) return;
    try {
      if (
        outcome.kind !== "none" &&
        (!attempt.isCurrent() && (outcome.kind !== "missing" || attempt.hasCurrent()))
      ) {
        handlers.onSuperseded?.(attempt.hasCurrent());
        return;
      }
      if (outcome.kind === "resumed") {
        handlers.onResume(outcome.state, {
          gameId: outcome.gameId,
          terminal: outcome.terminal,
        });
      } else if (outcome.kind === "failed") {
        handlers.onTransientError?.(outcome.error);
      } else if (outcome.kind === "superseded") {
        handlers.onSuperseded?.(attempt.hasCurrent());
      }
    } finally {
      if (subscribed) handlers.setPending(false);
    }
  });

  return () => {
    subscribed = false;
  };
}
