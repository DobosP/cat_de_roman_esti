// App.tsx — routing shell for the word-game arcade. Every screen is a real URL
// (shareable/bookmarkable; the FastAPI BFF serves index.html on deep links) and
// screen changes animate through AnimatePresence. Game logic lives per screen;
// the shell owns only toasts + transitions.

import { useCallback, useRef, useState, type ReactNode } from "react";
import { Navigate, Route, Routes, useLocation, useNavigate } from "react-router-dom";
import { AnimatePresence, motion, MotionConfig } from "framer-motion";
import { ToastStack, type ToastData, type ToastKind } from "@roedu/ui";
import Home from "./screens/Home";
import Alchimie from "./screens/Alchimie";
import CaldRece from "./screens/CaldRece";
import Lant from "./screens/Lant";
import Conexiuni from "./screens/Conexiuni";
import AccountBar from "./components/AccountBar";

export type { ToastKind };

const SCREEN_TRANSITION = { duration: 0.4, ease: [0.22, 1, 0.36, 1] as const };
const variants = {
  initial: { opacity: 0, scale: 0.985, y: 14 },
  enter: { opacity: 1, scale: 1, y: 0 },
  exit: { opacity: 0, scale: 1.01, y: -14 },
};

function ScreenFrame({ children }: { children: ReactNode }) {
  return (
    <motion.div
      className="screen"
      variants={variants}
      initial="initial"
      animate="enter"
      exit="exit"
      transition={SCREEN_TRANSITION}
    >
      {children}
    </motion.div>
  );
}

export default function App() {
  const location = useLocation();
  const navigate = useNavigate();
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

  const goHome = useCallback(() => navigate("/"), [navigate]);

  return (
    <MotionConfig reducedMotion="user">
      <div className="app-shell">
        <AccountBar />
        <AnimatePresence mode="wait">
          <Routes location={location} key={location.pathname}>
            <Route
              path="/"
              element={
                <ScreenFrame>
                  <Home onToast={pushToast} />
                </ScreenFrame>
              }
            />
            <Route
              path="/alchimie"
              element={
                <ScreenFrame>
                  <Alchimie onExit={goHome} onToast={pushToast} />
                </ScreenFrame>
              }
            />
            <Route
              path="/cald-rece"
              element={
                <ScreenFrame>
                  <CaldRece onExit={goHome} onToast={pushToast} />
                </ScreenFrame>
              }
            />
            <Route
              path="/lant"
              element={
                <ScreenFrame>
                  <Lant onExit={goHome} onToast={pushToast} />
                </ScreenFrame>
              }
            />
            <Route
              path="/conexiuni"
              element={
                <ScreenFrame>
                  <Conexiuni onExit={goHome} onToast={pushToast} />
                </ScreenFrame>
              }
            />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </AnimatePresence>

        <ToastStack toasts={toasts} onDismiss={dismissToast} />
      </div>
    </MotionConfig>
  );
}
