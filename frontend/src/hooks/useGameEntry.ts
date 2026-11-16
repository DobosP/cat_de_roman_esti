import { useCallback, useEffect, useLayoutEffect, useRef, useState } from "preact/hooks";
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
  const date = useRef(localDay());
  const isPresent = useIsPresent();
  const presentPreviously = useRef(isPresent);
  const parkedCandidate = useRef<string | null>(null);
  const replay = useRef(read(replayKey));
  const [options, setOptions] = useState(() => readFreeOptions(game));

  useLayoutEffect(() => {
    if (isPresent && !presentPreviously.current) {
      date.current = localDay();
      parkedCandidate.current = null;
      replay.current = read(replayKey);
      setOptions(readFreeOptions(game));
    }
    presentPreviously.current = isPresent;
  }, [game, isPresent, replayKey]);

  const admit = useCallback((round: Round, terminal: boolean) => {
    // A completion discovered by GET still belongs to the saved day, even if the
    // originating tab closed before it could persist the result.
    if (terminal) {
      if (round.daily) markDailyDone(game, round.daily);
      return true;
    }
    const decision = roundEntry(game, date.current, { ...round, terminal });
    if (decision.kind === "resume") {
      if (round.daily) markDailyStarted(game, round.daily);
      return true;
    }
    if (!round.daily) parkedCandidate.current = round.game_id;
    return false;
  }, [game]);

  const remember = useCallback((round: Round) => {
    if (round.daily) {
      if (parkedCandidate.current && active.isCurrent(parkedCandidate.current)) {
        write(parkedKey, parkedCandidate.current);
      }
      replay.current = dailyStatus(game, round.daily).started ? round.game_id : null;
      write(replayKey, replay.current);
      markDailyStarted(game, round.daily);
    } else {
      write(parkedKey, null);
    }
    parkedCandidate.current = null;
    active.remember(round.game_id);
  }, [active, game, parkedKey, replayKey]);

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
    ? replay.current === round.game_id ? "Reluare" : "Jocul zilei"
    : round || dailyStatus(game, date.current).done ? "Rundă liberă" : "Jocul zilei";

  const complete = useCallback((round: Round) => {
    if (round.daily) markDailyDone(game, round.daily);
  }, [game]);

  return {
    admit, remember, mode, isPresent, useParked, options,
    day: date.current,
    choose: () => roundEntry(game, date.current),
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
  const didStart = useRef(false);
  const latest = useRef({ entry, shouldStart, start, retryResume });
  useLayoutEffect(() => { latest.current = { entry, shouldStart, start, retryResume }; });
  const startEntry = (completedId?: string) => {
    const choice = entry.choose();
    if (choice.kind === "free" && entry.useParked(completedId)) retryResume();
    else start(choice.kind === "daily" ? choice.daily : undefined, completedId);
  };

  useEffect(() => {
    if (!entry.isPresent) { didStart.current = false; return; }
    const tryStart = () => {
      const { entry: current, shouldStart: ready, start: create, retryResume: resume } = latest.current;
      if (!current.isPresent || !ready || didStart.current || document.visibilityState !== "visible") return;
      const choice = current.choose();
      if (choice.kind === "free" && current.useParked()) resume();
      else {
        didStart.current = true;
        create(choice.kind === "daily" ? choice.daily : undefined);
      }
    };
    tryStart();
    document.addEventListener("visibilitychange", tryStart);
    return () => document.removeEventListener("visibilitychange", tryStart);
  }, [entry.isPresent, shouldStart]);

  return startEntry;
}
