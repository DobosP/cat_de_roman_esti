import { useCallback, useEffect, useLayoutEffect, useMemo, useRef, useState } from "preact/hooks";
import { useIsPresent } from "@roedu/ui/motion";
import { ApiError } from "../api/client";
import type { ActiveGameMemo } from "./useActiveGame";
import { useDailyIntent } from "./useDailyIntent";
import { todayLocal } from "../share";
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
  dismissRecovery: () => void;
}

interface SavedGameResumeOptions<T> {
  active: ActiveGameMemo;
  load: (gameId: string) => Promise<T>;
  isTerminal: (state: T) => boolean;
  setPending: (pending: boolean) => void;
  onResume: (state: T, detail: { gameId: string; terminal: boolean; bypassed: boolean }) => void;
  /** A circuit visit (`?challenge=daily`) resumed an unfinished free round instead. */
  onDailyBypassed?: () => void;
  /** Retire local presentation before a retained frame reads its saved session again. */
  onReentry?: () => void;
}

/** Resume one saved server session without owning any game-specific screen state. */
export function useSavedGameResume<T>({
  active,
  load,
  isTerminal,
  setPending,
  onResume,
  onDailyBypassed,
  onReentry,
}: SavedGameResumeOptions<T>): SavedGameResumeControl {
  const [generation, setGeneration] = useState(0);
  const [recovery, setRecovery] = useState<ResumeRecovery | null>(null);
  const unsubscribeRef = useRef<(() => void) | null>(null);
  const isPresent = useIsPresent(), presentRef = useRef(true);
  const departedRef = useRef(false), reentryRef = useRef(onReentry);
  useLayoutEffect(() => { reentryRef.current = onReentry; });
  useLayoutEffect(() => {
    presentRef.current = isPresent;
    if (!isPresent) { departedRef.current = true; unsubscribeRef.current?.(); }
    else if (departedRef.current) {
      departedRef.current = false;
      setRecovery(null);
      reentryRef.current?.();
    }
    return () => { presentRef.current = false; unsubscribeRef.current?.(); };
  }, [isPresent]);
  const dailyIntent = useDailyIntent();
  // Read at resume time without resubscribing: the callbacks change every render.
  // Returns whether the bypass notice was shown, so the screen skips its own resume toast.
  const dailyResumeRef = useRef<(daily: unknown, terminal: boolean) => boolean>(() => false);
  useEffect(() => {
    dailyResumeRef.current = (daily, terminal) => {
      if (!presentRef.current) return false;
      if (!dailyIntent.active) return false;
      // Today's resumed daily fulfils the circuit intent. An older day's daily or a
      // free round keeps it for later; only an unfinished free round is announced.
      if (daily === todayLocal()) dailyIntent.consume();
      else if (!daily && !terminal && onDailyBypassed) {
        onDailyBypassed();
        return true;
      }
      return false;
    };
  });
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
    [active, generation, isTerminal, load, isPresent],
  );

  useEffect(() => {
    if (!isPresent) return;
    const unsubscribe = subscribeSavedGameResume(attempt, {
        setPending: (pending) => { if (presentRef.current) setPending(pending); },
        onResume: (state, detail) => {
          if (!presentRef.current) return;
          setRecovery(null);
          const bypassed = dailyResumeRef.current((state as { daily?: unknown }).daily, detail.terminal);
          onResume(state, { ...detail, bypassed });
        },
        onTransientError: () => { if (presentRef.current) setRecovery({ kind: "failed" }); },
        onSuperseded: (hasCurrent) => { if (presentRef.current) setRecovery({ kind: "changed", hasCurrent }); },
      });
    unsubscribeRef.current = unsubscribe;
    return () => {
      unsubscribe();
      if (unsubscribeRef.current === unsubscribe) unsubscribeRef.current = null;
    };
  }, [attempt, onResume, setPending, isPresent]);

  const retryResume = useCallback(() => {
    if (!presentRef.current) return;
    unsubscribeRef.current?.();
    setRecovery(null);
    setGeneration((value) => value + 1);
  }, []);

  const cancelResume = useCallback(() => {
    unsubscribeRef.current?.();
  }, []);

  const dismissRecovery = useCallback(() => setRecovery(null), []);

  return { recovery, retryResume, cancelResume, dismissRecovery };
}
