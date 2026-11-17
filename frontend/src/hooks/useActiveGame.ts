// useActiveGame — remembers the server-side game id of a RUNNING game so a page
// refresh or a revisited deep link resumes the session (via the game's GET
// /games/{id}) instead of silently dropping it. Stored in localStorage keyed per
// game; the server's sliding 7,200-second (2h) session TTL is the natural expiry — a dead id
// simply 404s and the screen falls back to its intro.

import { useMemo } from "preact/hooks";
import type { GameKey } from "../games";
import { readLocalValue, writeLocalValue } from "../pageStorage";

const PREFIX = "cat_active_game_v1_";

export interface ActiveGameMemo {
  /** Remember a live game id (call right after a successful create). */
  remember: (gameId: string) => void;
  /** Forget it (call when the game finishes or the player starts fresh). */
  forget: () => void;
  /** Forget `gameId` only while it is still the remembered game. */
  forgetIfCurrent: (gameId: string) => boolean;
  /** Whether `gameId` is still the remembered game. */
  isCurrent: (gameId: string) => boolean;
  /** The remembered id for this game, if any. */
  peek: () => string | null;
}

export function useActiveGame(game: GameKey): ActiveGameMemo {
  return useMemo(() => {
    const key = `${PREFIX}${game}`;
    return {
      remember: (gameId: string) => {
        writeLocalValue(key, gameId);
      },
      forget: () => {
        writeLocalValue(key, null);
      },
      forgetIfCurrent: (gameId: string) => {
        if (readLocalValue(key) !== gameId) return false;
        writeLocalValue(key, null);
        return true;
      },
      isCurrent: (gameId: string) => {
        return readLocalValue(key) === gameId;
      },
      peek: () => {
        return readLocalValue(key);
      },
    };
  }, [game]);
}
