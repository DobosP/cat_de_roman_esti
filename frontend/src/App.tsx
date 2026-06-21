import { useCallback, useReducer, useRef, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import type { GameState } from "./api/types";
import { Menu } from "./screens/Menu";
import { Game } from "./screens/Game";
import { Win } from "./screens/Win";
import { ToastStack, type ToastData, type ToastKind } from "./components/Toast";

// ---------------------------------------------------------------- state machine
// A tiny screen router as a useReducer FSM (zustand-free). Screens: menu -> game -> win.
// The active GameState lives here so Game/Win share one server-authoritative object.

type Screen = "menu" | "game" | "win";

interface AppState {
  screen: Screen;
  game: GameState | null;
}

type Action =
  | { type: "to_menu" }
  | { type: "start"; game: GameState }
  | { type: "sync"; game: GameState };

function reducer(state: AppState, action: Action): AppState {
  switch (action.type) {
    case "to_menu":
      return { screen: "menu", game: null };
    case "start":
      return { screen: "game", game: action.game };
    case "sync": {
      // The server tells us when the game is won; route to Win on the won transition.
      const screen: Screen = action.game.won ? "win" : "game";
      return { screen, game: action.game };
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
  const [state, dispatch] = useReducer(reducer, { screen: "menu", game: null });
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

  const handleStart = useCallback((game: GameState) => {
    dispatch({ type: "start", game });
  }, []);

  const handleSync = useCallback((game: GameState) => {
    dispatch({ type: "sync", game });
  }, []);

  const handleMenu = useCallback(() => {
    dispatch({ type: "to_menu" });
  }, []);

  // Replay restarts the same puzzle; the Game screen owns the reset call and hands us
  // back the fresh state through onSync, so here we just route back to the board.
  const handleReplay = useCallback((game: GameState) => {
    dispatch({ type: "start", game });
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
