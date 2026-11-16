import { useCallback, useEffect, useLayoutEffect, useState } from "preact/hooks";
import { useEventValue } from "./useEventValue";
import { useIsPresent } from "@roedu/ui/motion";
import { dailyStatus, localDay, markDailyDone, markDailyStarted, readFreeOptions, roundEntry, writeFreeOptions } from "../entry";
import type { GameKey } from "../games";
import type { ActiveGameMemo } from "./useActiveGame";

interface Round {
  game_id: string;
  daily?: string;
}

function read(key: string): string | null {
  try { return localStorage.getItem(key); } catch { return null; }
}

function write(key: string, value: string | null) {
  try {
    if (value === null) localStorage.removeItem(key);
    else localStorage.setItem(key, value);
  } catch { /* A browser without storage starts with a fresh entry each visit. */ }
}

export function useGameEntry(game: GameKey, active: ActiveGameMemo) {
  const parkedKey = `cat_parked_free_v2_${game}`;
  const replayKey = `cat_replay_v2_${game}`;
  const [date, setDate] = useState(localDay);
  const isPresent = useIsPresent();
  const presentPreviously = useEventValue<boolean>(false);
  const initialized = useEventValue<boolean>(false);
  const parkedCandidate = useEventValue<string | null>(null);
  const [replay, setReplay] = useState(() => read(replayKey));
  const [recoveredTerminal, setRecoveredTerminal] = useState<string | null>(null);
  const presentingRecovery = useEventValue<boolean>(false);
  const [settledTerminal, setSettledTerminal] = useState<string | null>(null);
  const [options, setOptions] = useState(() => readFreeOptions(game));

  useLayoutEffect(() => {
    if (isPresent && initialized.read() && !presentPreviously.read()) {
      setDate(localDay());
      parkedCandidate.write(null);
      setRecoveredTerminal(null);
      presentingRecovery.write(false);
      setSettledTerminal(null);
      setReplay(read(replayKey));
      setOptions(readFreeOptions(game));
    }
    presentPreviously.write(isPresent);
    initialized.write(true);
  }, [game, initialized, isPresent, parkedCandidate, presentPreviously, presentingRecovery, replayKey]);

  const admit = useCallback((round: Round, terminal: boolean) => {
    setReplay(read(replayKey));
    // A completion discovered by GET still belongs to the saved day, even if the
    // originating tab closed before it could persist the result.
    if (terminal) {
      setRecoveredTerminal(presentingRecovery.read() ? null : round.game_id);
      presentingRecovery.write(false);
      if (round.daily) markDailyDone(game, round.daily);
      return true;
    }
    presentingRecovery.write(false);
    setSettledTerminal(null);
    setRecoveredTerminal(null);
    const decision = roundEntry(game, date, { ...round, terminal });
    if (decision.kind === "resume") {
      if (round.daily) markDailyStarted(game, round.daily);
      return true;
    }
    if (!round.daily) parkedCandidate.write(round.game_id);
    return false;
  }, [date, game, parkedCandidate, presentingRecovery, replayKey]);

  const remember = useCallback((round: Round, expected: string | null) => {
    // Another tab may have started a newer game while this POST was in flight.
    const current = active.peek();
    if (current !== null && current !== expected) return false;
    if (round.daily) {
      const candidate = parkedCandidate.read();
      if (candidate && active.isCurrent(candidate)) {
        write(parkedKey, candidate);
      }
      const replayId = dailyStatus(game, round.daily).started ? round.game_id : null;
      setReplay(replayId);
      write(replayKey, replayId);
      markDailyStarted(game, round.daily);
    } else {
      write(parkedKey, null);
    }
    parkedCandidate.write(null);
    active.remember(round.game_id);
    return true;
  }, [active, game, parkedCandidate, parkedKey, replayKey]);

  const useParked = (completedId?: string) => {
    const activeId = active.peek();
    if (activeId && activeId !== completedId) return false;
    const parked = read(parkedKey);
    if (!parked) return false;
    active.remember(parked);
    write(parkedKey, null);
    return active.isCurrent(parked);
  };

  const mode = (round: Round | null) => round?.daily
    ? replay === round.game_id ? "Reluare" : "Jocul zilei"
    : round || dailyStatus(game, date).done ? "Rundă liberă" : "Jocul zilei";

  const complete = useCallback((round: Round) => {
    if (round.daily) markDailyDone(game, round.daily);
  }, [game]);

  const settleCompletion = useCallback((round: Round) => {
    active.forgetIfCurrent(round.game_id);
    if (recoveredTerminal === round.game_id && presentPreviously.read()) {
      setSettledTerminal(round.game_id);
    }
  }, [active, presentPreviously, recoveredTerminal]);
  return {
    admit, remember, mode, isPresent, useParked, options, settleCompletion,
    recoveredTerminal: (round: Round | null) => round !== null && recoveredTerminal === round.game_id,
    readyAfterTerminal: (round: Round | null) => round !== null && settledTerminal === round.game_id,
    presentRecovery: () => { presentingRecovery.write(true); },
    newerSavedRound: () => settledTerminal !== null && active.peek() !== null,
    day: date,
    choose: () => roundEntry(game, date),
    complete,
    updateOptions: (next: typeof options) => { writeFreeOptions(game, next); setOptions(next); },
  } as const;
}

type GameEntry = ReturnType<typeof useGameEntry>;

/** Wait for the saved-round read and a visible screen before creating a round. */
export function useRoundStart(
  entry: GameEntry,
  shouldStart: boolean,
  retryResume: () => void,
  start: (daily?: string, previousGameId?: string) => void,
) {
  const didStart = useEventValue<boolean>(false);
  const latest = useEventValue<{ entry: GameEntry; shouldStart: boolean; start: typeof start; retryResume: typeof retryResume } | null>(null);
  useLayoutEffect(() => { latest.write({ entry, shouldStart, start, retryResume }); });
  const startEntry = (completedId?: string) => {
    const choice = entry.choose();
    if (choice.kind === "free" && entry.useParked(completedId)) retryResume();
    else start(choice.kind === "daily" ? choice.daily : undefined, completedId);
  };

  useEffect(() => {
    if (!entry.isPresent || !shouldStart) { didStart.write(false); return; }
    const tryStart = () => {
      const pending = latest.read();
      if (!pending) return;
      const { entry: current, shouldStart: ready, start: create, retryResume: resume } = pending;
      if (!current.isPresent || !ready || didStart.read() || document.visibilityState !== "visible") return;
      const choice = current.choose();
      if (current.newerSavedRound() || (choice.kind === "free" && current.useParked())) {
        didStart.write(true);
        resume();
      }
      else {
        didStart.write(true);
        create(choice.kind === "daily" ? choice.daily : undefined);
      }
    };
    tryStart();
    document.addEventListener("visibilitychange", tryStart);
    return () => document.removeEventListener("visibilitychange", tryStart);
  }, [didStart, entry.isPresent, latest, shouldStart]);

  return startEntry;
}
