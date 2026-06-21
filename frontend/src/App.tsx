import { useCallback, useEffect, useReducer, useRef, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import type { GameState } from "./api/types";
import { Menu } from "./screens/Menu";
import { Game } from "./screens/Game";
import { Win } from "./screens/Win";
import { ToastStack, type ToastData, type ToastKind } from "./components/Toast";
import { recordRun } from "./leaderboard";

// ---------------------------------------------------------------- state machine
// A tiny screen router as a useReducer FSM (zustand-free). Screens: menu -> game -> win.
// The active GameState lives here so Game/Win share one server-authoritative object.
//
// A "run" is a multi-puzzle session: starting from the Menu opens a fresh run, and each
// "Urmatoarea" (Next) keeps playing within it. We tally how many distinct puzzles were
// solved and the cumulative score; each won game is counted exactly once (keyed by
// game_id, so replaying the same puzzle never double-counts).

type Screen = "menu" | "game" | "win";

export interface RunState {
  solved: number;
  total: number;
  /** game_ids already counted into this run (avoids double-counting on replay/resync). */
  counted: string[];
}

const EMPTY_RUN: RunState = { solved: 0, total: 0, counted: [] };

interface AppState {
  screen: Screen;
  game: GameState | null;
  run: RunState;
}

type Action =
  | { type: "to_menu" }
  // `fresh` starts a NEW run (from the Menu); otherwise we keep the current run (Next).
  | { type: "start"; game: GameState; fresh: boolean }
  | { type: "sync"; game: GameState };

function reducer(state: AppState, action: Action): AppState {
  switch (action.type) {
    case "to_menu":
      return { screen: "menu", game: null, run: EMPTY_RUN };
    case "start":
      return {
        screen: "game",
        game: action.game,
        run: action.fresh ? EMPTY_RUN : state.run,
      };
    case "sync": {
      // The server tells us when the game is won; route to Win on the won transition.
      const screen: Screen = action.game.won ? "win" : "game";
      let run = state.run;
      if (action.game.won && !run.counted.includes(action.game.game_id)) {
        run = {
          solved: run.solved + 1,
          total: run.total + action.game.score,
          counted: [...run.counted, action.game.game_id],
        };
      }
      return { screen, game: action.game, run };
    }
    default:
      return state;
  }
}

const SCREEN_TRANSITION = { duration: 0.45, ease: [0.22, 1, 0.36, 1] as const };

const variants = {
  initial: { opacity: 0, scale: 0.985, y: 14 },
  enter: { opacity: 1, scale: 1, y: 0 },
  exit: { opacity: 0, scale: 1.01, y: -14 },
};

export default function App() {
  const [state, dispatch] = useReducer(reducer, {
    screen: "menu",
    game: null,
    run: EMPTY_RUN,
  });
  const [toasts, setToasts] = useState<ToastData[]>([]);
  const toastId = useRef(0);

  const dismissToast = useCallback((id: number) => {
    setToasts((ts) => ts.filter((t) => t.id !== id));
  }, []);

  const pushToast = useCallback(
    (message: string, kind: ToastKind = "info") => {
      const id = ++toastId.current;
      setToasts((ts) => [...ts, { id, kind, message }]);
      window.setTimeout(() => dismissToast(id), 3600);
    },
    [dismissToast],
  );

  // Bank the run as a possible best as soon as it grows — recordRun only overwrites a
  // strictly higher total, so recording on every win (not just on exit) is safe and
  // means a strong run isn't lost if the player closes/reloads without hitting "Meniu".
  useEffect(() => {
    if (state.run.total > 0) recordRun(state.run.solved, state.run.total);
  }, [state.run.total, state.run.solved]);

  // From the Menu: a brand-new run.
  const handleStart = useCallback((game: GameState) => {
    dispatch({ type: "start", game, fresh: true });
  }, []);

  const handleSync = useCallback((game: GameState) => {
    dispatch({ type: "sync", game });
  }, []);

  const handleMenu = useCallback(() => {
    dispatch({ type: "to_menu" });
  }, []);

  // Replay (same puzzle) / Next (new puzzle) continue the CURRENT run; the Win screen
  // owns the reset/create call and hands us back the fresh state to route to the board.
  const handleReplay = useCallback((game: GameState) => {
    dispatch({ type: "start", game, fresh: false });
  }, []);

  return (
    <div className="app-shell">
      <AnimatePresence mode="wait">
        {state.screen === "menu" && (
          <motion.div
            key="menu"
            className="screen"
            variants={variants}
            initial="initial"
            animate="enter"
            exit="exit"
            transition={SCREEN_TRANSITION}
          >
            <Menu onStart={handleStart} onError={(m) => pushToast(m, "error")} />
          </motion.div>
        )}

        {state.screen === "game" && state.game && (
          <motion.div
            key="game"
            className="screen"
            variants={variants}
            initial="initial"
            animate="enter"
            exit="exit"
            transition={SCREEN_TRANSITION}
          >
            <Game
              game={state.game}
              run={state.run}
              onSync={handleSync}
              onExit={handleMenu}
              onToast={pushToast}
            />
          </motion.div>
        )}

        {state.screen === "win" && state.game && (
          <motion.div
            key="win"
            className="screen"
            variants={variants}
            initial="initial"
            animate="enter"
            exit="exit"
            transition={SCREEN_TRANSITION}
          >
            <Win
              game={state.game}
              run={state.run}
              onReplay={handleReplay}
              onMenu={handleMenu}
              onToast={pushToast}
            />
          </motion.div>
        )}
      </AnimatePresence>

      <ToastStack toasts={toasts} onDismiss={dismissToast} />
    </div>
  );
}
