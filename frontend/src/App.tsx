import { useCallback, useRef, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import Alchimie from "./screens/Alchimie";
import CaldRece from "./screens/CaldRece";
import Lant from "./screens/Lant";
import Conexiuni from "./screens/Conexiuni";
import { SoundToggle } from "./components/SoundToggle";
import { ToastStack, type ToastData, type ToastKind } from "./components/Toast";
import { sound } from "./sound";

// ---------------------------------------------------------------- arcade router
// The whole app is now a text-only word-game arcade over the Romanian concept graph —
// no graph visualization. A tiny screen router (home -> one of three games) holds the
// active game key; each game is a self-contained server-authoritative screen.

type GameKey = "alchimie" | "contexto" | "lant" | "conexiuni";

interface GameDef {
  key: GameKey;
  title: string;
  tag: string; // the Twitch-familiar concept it riffs on
  blurb: string;
  accent: string;
  glow: string;
  icon: string;
}

const GAMES: GameDef[] = [
  {
    key: "alchimie",
    title: "Alchimie",
    tag: "à la Infinite Craft",
    blurb:
      "Combina doua concepte ca sa descoperi unul nou. Creste-ti inventarul pas cu pas pana cand croiesti conceptul-tinta.",
    accent: "#c08bff",
    glow: "#dcc0ff",
    icon: "⚗️",
  },
  {
    key: "contexto",
    title: "Cald sau Rece",
    tag: "à la Contexto",
    blurb:
      "Un concept secret te asteapta. Fiecare incercare iti spune cat de aproape esti — de la inghetat la fierbinte. Gaseste-l.",
    accent: "#ff7a59",
    glow: "#ffc7a0",
    icon: "🔥",
  },
  {
    key: "lant",
    title: "Lantul Cuvintelor",
    tag: "à la The Wiki Game",
    blurb:
      "De la START la TINTA: scrie de fiecare data un concept legat de cel curent si sari din cuvant in cuvant, in cat mai putine miscari.",
    accent: "#56d4dd",
    glow: "#a3eef2",
    icon: "🔗",
  },
  {
    key: "conexiuni",
    title: "Conexiuni",
    tag: "à la NYT Connections",
    blurb:
      "Saisprezece concepte, patru categorii ascunse. Grupeaza-le cate patru — ai voie la patru greseli.",
    accent: "#5fd99b",
    glow: "#a7f0c8",
    icon: "🧩",
  },
];

const SCREEN_TRANSITION = { duration: 0.4, ease: [0.22, 1, 0.36, 1] as const };
const variants = {
  initial: { opacity: 0, scale: 0.985, y: 14 },
  enter: { opacity: 1, scale: 1, y: 0 },
  exit: { opacity: 0, scale: 1.01, y: -14 },
};

export default function App() {
  const [active, setActive] = useState<GameKey | null>(null);
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

  const openGame = useCallback((key: GameKey) => {
    sound.unlockAudio();
    sound.playSelect();
    setActive(key);
  }, []);

  const goHome = useCallback(() => setActive(null), []);

  return (
    <div className="app-shell">
      <AnimatePresence mode="wait">
        {active === null && (
          <motion.div
            key="home"
            className="screen"
            variants={variants}
            initial="initial"
            animate="enter"
            exit="exit"
            transition={SCREEN_TRANSITION}
          >
            <Home onOpen={openGame} />
          </motion.div>
        )}

        {active === "alchimie" && (
          <motion.div key="alchimie" className="screen" variants={variants} initial="initial" animate="enter" exit="exit" transition={SCREEN_TRANSITION}>
            <Alchimie onExit={goHome} onToast={pushToast} />
          </motion.div>
        )}

        {active === "contexto" && (
          <motion.div key="contexto" className="screen" variants={variants} initial="initial" animate="enter" exit="exit" transition={SCREEN_TRANSITION}>
            <CaldRece onExit={goHome} onToast={pushToast} />
          </motion.div>
        )}

        {active === "lant" && (
          <motion.div key="lant" className="screen" variants={variants} initial="initial" animate="enter" exit="exit" transition={SCREEN_TRANSITION}>
            <Lant onExit={goHome} onToast={pushToast} />
          </motion.div>
        )}

        {active === "conexiuni" && (
          <motion.div key="conexiuni" className="screen" variants={variants} initial="initial" animate="enter" exit="exit" transition={SCREEN_TRANSITION}>
            <Conexiuni onExit={goHome} onToast={pushToast} />
          </motion.div>
        )}
      </AnimatePresence>

      <ToastStack toasts={toasts} onDismiss={dismissToast} />
    </div>
  );
}

// ------------------------------------------------------------------------- home
function Home({ onOpen }: { onOpen: (key: GameKey) => void }) {
  return (
    <div className="screen-pad fill" style={{ overflowY: "auto" }}>
      <div className="container col" style={{ gap: 28, paddingBlock: 16 }}>
        <header className="col" style={{ gap: 10 }}>
          <div className="row spread" style={{ gap: 12, alignItems: "flex-start" }}>
            <motion.h1
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, ease: [0.22, 1, 0.36, 1] }}
              style={{ fontSize: "clamp(2rem, 5vw, 3.4rem)", lineHeight: 1.02 }}
            >
              cat de roman{" "}
              <span
                style={{
                  background: "linear-gradient(120deg, var(--accent), var(--accent-2))",
                  WebkitBackgroundClip: "text",
                  backgroundClip: "text",
                  color: "transparent",
                }}
              >
                esti
              </span>
              ?
            </motion.h1>
            <SoundToggle />
          </div>
          <motion.p
            className="muted"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.15, duration: 0.5 }}
            style={{ maxWidth: 640, fontSize: "1.05rem", margin: 0 }}
          >
            Trei jocuri de cuvinte peste reteaua semantica a culturii romanesti. Combina,
            ghiceste sau inlantuie concepte — si ajunge la destinatie.
          </motion.p>
        </header>

        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fill, minmax(min(100%, 280px), 1fr))",
            gap: 16,
          }}
        >
          {GAMES.map((g, i) => (
            <motion.button
              key={g.key}
              type="button"
              onClick={() => onOpen(g.key)}
              initial={{ opacity: 0, y: 18 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.06 * i, duration: 0.4 }}
              whileHover={{ y: -4 }}
              whileTap={{ scale: 0.98 }}
              className="card"
              style={{
                textAlign: "left",
                padding: 22,
                cursor: "pointer",
                position: "relative",
                overflow: "hidden",
                borderColor: "var(--surface-border)",
                boxShadow: "var(--shadow-card)",
                display: "grid",
                gap: 10,
              }}
            >
              <div
                aria-hidden
                style={{
                  position: "absolute",
                  inset: 0,
                  background: `radial-gradient(160px 110px at 100% 0%, ${g.glow}22, transparent 70%)`,
                  pointerEvents: "none",
                }}
              />
              <div className="row spread" style={{ position: "relative" }}>
                <span style={{ fontSize: "1.9rem" }} aria-hidden>
                  {g.icon}
                </span>
                <span className="chip" style={{ fontSize: "0.7rem", borderColor: g.accent, color: g.accent }}>
                  {g.tag}
                </span>
              </div>
              <strong
                style={{
                  position: "relative",
                  fontFamily: "var(--font-display)",
                  fontSize: "1.3rem",
                  color: g.accent,
                }}
              >
                {g.title}
              </strong>
              <p className="muted" style={{ position: "relative", margin: 0, fontSize: "0.9rem" }}>
                {g.blurb}
              </p>
              <span
                className="row"
                style={{
                  position: "relative",
                  gap: 6,
                  marginTop: 4,
                  color: g.accent,
                  fontWeight: 600,
                  fontSize: "0.9rem",
                }}
              >
                Joaca →
              </span>
            </motion.button>
          ))}
        </div>

        <p className="faint" style={{ fontSize: "0.8rem" }}>
          Toate cele trei jocuri ruleaza pe acelasi graf de ~250 de concepte romanesti.
        </p>
      </div>
    </div>
  );
}
