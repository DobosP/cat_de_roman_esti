// Framework-free saved-game resume lifecycle. React uses the subscription wrapper
// below so StrictMode can unsubscribe and immediately resubscribe to the same
// single-flight request, while a real unmount receives no late callbacks.

/**
 * @template T
 * @param {{
 *   active: {peek: () => string | null, forget: () => void},
 *   load: (gameId: string) => Promise<T>,
 *   isTerminal: (state: T) => boolean,
 *   terminal: "adopt" | "discard",
 *   transient: "forget" | "retain",
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
      const terminal = options.isTerminal(state);
      if (terminal && options.terminal === "discard") {
        options.active.forget();
        return { kind: "terminal-discarded", gameId: savedId, state };
      }
      return { kind: "resumed", gameId: savedId, state, terminal };
    } catch (error) {
      if (options.isMissing(error)) {
        options.active.forget();
        return { kind: "missing", gameId: savedId, error };
      }
      if (options.transient === "forget") options.active.forget();
      return { kind: "failed", gameId: savedId, error };
    }
  };

  return {
    hasSavedGame: savedId !== null && savedId !== "",
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
      if (outcome.kind === "resumed") {
        handlers.onResume(outcome.state, {
          gameId: outcome.gameId,
          terminal: outcome.terminal,
        });
      } else if (outcome.kind === "failed") {
        handlers.onTransientError?.(outcome.error);
      }
    } finally {
      if (subscribed) handlers.setPending(false);
    }
  });

  return () => {
    subscribed = false;
  };
}
