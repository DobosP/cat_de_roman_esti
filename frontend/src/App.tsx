import { useCallback, useMemo, useRef, useState } from "react";
import { AnimatePresence, motion, MotionConfig } from "framer-motion";
import Alchimie from "./screens/Alchimie";
import CaldRece from "./screens/CaldRece";
import Lant from "./screens/Lant";
import Conexiuni from "./screens/Conexiuni";
import { SoundToggle } from "./components/SoundToggle";
import { ToastStack, type ToastData, type ToastKind } from "./components/Toast";
import { sound } from "./sound";
import {
  exportScores,
  importScores,
  scoreBoard,
  type GameScoreEntry,
  type ScoreEntry,
} from "./scores";
import { todayLocal } from "./share";

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
    <MotionConfig reducedMotion="user">
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
            <Home onOpen={openGame} onToast={pushToast} />
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
    </MotionConfig>
  );
}

// ------------------------------------------------------------------------- home
type HistoryTab = "top" | "today" | "recent";

const GAME_TITLES: Record<GameKey, string> = {
  alchimie: "Alchimie",
  contexto: "Cald sau Rece",
  lant: "Lantul Cuvintelor",
  conexiuni: "Conexiuni",
};

function Home({
  onOpen,
  onToast,
}: {
  onOpen: (key: GameKey) => void;
  onToast: (message: string, kind?: ToastKind) => void;
}) {
  const [historyTab, setHistoryTab] = useState<HistoryTab>("top");
  const [gameFilter, setGameFilter] = useState<GameKey | "all">("all");
  const [board, setBoard] = useState(() => scoreBoard());
  const fileRef = useRef<HTMLInputElement>(null);
  const today = todayLocal();
  const totals = useMemo(
    () => GAMES.map((game) => ({ ...game, record: board[game.key] })),
    [board],
  );
  const allRows = useMemo(
    () =>
      Object.entries(board)
        .flatMap(([game, record]) => record.recent.map((entry) => ({ ...entry, game })))
        .sort((a, b) => b.at - a.at),
    [board],
  );
  const topRows = useMemo(
    () =>
      Object.entries(board)
        .flatMap(([game, record]) => (record.best ? [{ ...record.best, game }] : []))
        .sort((a, b) => b.score - a.score || b.at - a.at)
        .slice(0, 12),
    [board],
  );
  const todayRows = useMemo(
    () => allRows.filter((entry) => entry.daily === today).slice(0, 20),
    [allRows, today],
  );
  const recentRows = useMemo(
    () =>
      allRows
        .filter((entry) => gameFilter === "all" || entry.game === gameFilter)
        .slice(0, 30),
    [allRows, gameFilter],
  );
  const playedTotal = totals.reduce((sum, row) => sum + (row.record?.played ?? 0), 0);

  const handleExport = useCallback(() => {
    const blob = new Blob([exportScores()], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `cat-de-roman-istoric-${todayLocal()}.json`;
    a.click();
    URL.revokeObjectURL(url);
    onToast("Istoricul local a fost exportat.", "success");
  }, [onToast]);

  const handleImport = useCallback(
    async (event: React.ChangeEvent<HTMLInputElement>) => {
      const file = event.target.files?.[0];
      event.target.value = "";
      if (!file) return;
      try {
        const outcome = importScores(await file.text());
        setBoard(scoreBoard());
        onToast(
          `Importat: ${outcome.entries} rezultate in ${outcome.games} jocuri.`,
          "success",
        );
      } catch (err) {
        onToast(err instanceof Error ? err.message : "Import invalid.", "error");
      }
    },
    [onToast],
  );

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
            Patru jocuri de cuvinte peste reteaua semantica a culturii romanesti. Combina,
            ghiceste, inlantuie sau grupeaza concepte — si ajunge la destinatie.
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
              aria-label={`Joaca ${g.title} — ${g.tag}`}
              initial={{ opacity: 0, y: 18 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.06 * i, duration: 0.4 }}
              whileHover={{ y: -4 }}
              whileTap={{ scale: 0.98 }}
              className="card game-card"
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

        <section className="col" style={{ gap: 14 }}>
          <div className="row spread wrap" style={{ gap: 12, alignItems: "center" }}>
            <div className="row wrap" style={{ gap: 8 }}>
              {(["top", "today", "recent"] as const).map((tab) => (
                <button
                  key={tab}
                  type="button"
                  className={`btn ${historyTab === tab ? "btn-primary" : "btn-ghost"}`}
                  onClick={() => setHistoryTab(tab)}
                  style={{ padding: "9px 13px", borderRadius: 12 }}
                >
                  {tab === "top" ? "Top" : tab === "today" ? "Azi" : "Istoric"}
                </button>
              ))}
            </div>
            <div className="row wrap" style={{ gap: 8 }}>
              <button
                type="button"
                className="btn btn-ghost"
                onClick={handleExport}
                disabled={playedTotal === 0}
                style={{ padding: "9px 13px", borderRadius: 12 }}
              >
                <span aria-hidden>⬇</span> Export
              </button>
              <button
                type="button"
                className="btn btn-ghost"
                onClick={() => fileRef.current?.click()}
                style={{ padding: "9px 13px", borderRadius: 12 }}
              >
                <span aria-hidden>⬆</span> Import
              </button>
              <input
                ref={fileRef}
                type="file"
                accept="application/json,.json"
                onChange={handleImport}
                style={{ display: "none" }}
              />
            </div>
          </div>

          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fit, minmax(min(100%, 170px), 1fr))",
              gap: 10,
            }}
          >
            {totals.map((row) => (
              <div key={row.key} className="card" style={{ padding: 14, display: "grid", gap: 8 }}>
                <div className="row spread" style={{ gap: 8 }}>
                  <span className="chip" style={{ borderColor: row.accent, color: row.accent }}>
                    {row.title}
                  </span>
                  <strong style={{ fontVariantNumeric: "tabular-nums" }}>
                    {row.record?.played ?? 0}
                  </strong>
                </div>
                <ScoreLine entry={row.record?.best ?? null} accent={row.accent} empty="Fara scor" />
              </div>
            ))}
          </div>

          {historyTab === "recent" && (
            <label className="row" style={{ gap: 8, alignSelf: "flex-start" }}>
              <span className="faint" style={{ fontSize: "0.78rem" }}>Joc</span>
              <select
                value={gameFilter}
                onChange={(event) => setGameFilter(event.target.value as GameKey | "all")}
                className="field"
                style={{ width: 210, padding: "9px 12px" }}
              >
                <option value="all">Toate</option>
                {GAMES.map((game) => (
                  <option key={game.key} value={game.key}>
                    {game.title}
                  </option>
                ))}
              </select>
            </label>
          )}

          <HistoryRows
            rows={
              historyTab === "top"
                ? topRows
                : historyTab === "today"
                  ? todayRows
                  : recentRows
            }
            empty={
              historyTab === "top"
                ? "Nu ai scoruri locale inca."
                : historyTab === "today"
                  ? "Niciun zilnic terminat azi."
                  : "Istoricul local este gol."
            }
          />
        </section>

        <p className="faint" style={{ fontSize: "0.8rem" }}>
          Toate cele patru jocuri ruleaza pe acelasi graf de 325 de concepte romanesti.
        </p>
      </div>
    </div>
  );
}

function HistoryRows({ rows, empty }: { rows: GameScoreEntry[]; empty: string }) {
  if (rows.length === 0) {
    return (
      <div className="card center muted" style={{ minHeight: 82, padding: 18 }}>
        {empty}
      </div>
    );
  }
  return (
    <div className="col" style={{ gap: 8 }}>
      {rows.map((entry, index) => (
        <div
          key={`${entry.game}-${entry.at}-${entry.score}-${index}`}
          className="card row spread wrap"
          style={{ gap: 12, padding: "12px 14px", alignItems: "center" }}
        >
          <div className="row" style={{ gap: 10, minWidth: 0 }}>
            <span className="faint" style={{ width: 24, textAlign: "right" }}>
              {index + 1}
            </span>
            <div className="col" style={{ gap: 2, minWidth: 0 }}>
              <strong>{GAME_TITLES[entry.game as GameKey] ?? entry.game}</strong>
              <span className="muted" style={{ fontSize: "0.84rem" }}>
                {entry.detail}
              </span>
            </div>
          </div>
          <div className="row" style={{ gap: 12, alignItems: "center" }}>
            <span className="faint" style={{ fontSize: "0.78rem" }}>
              {formatWhen(entry.at)}
            </span>
            <strong style={{ fontVariantNumeric: "tabular-nums" }}>{entry.score}</strong>
          </div>
        </div>
      ))}
    </div>
  );
}

function ScoreLine({
  entry,
  accent,
  empty,
}: {
  entry: ScoreEntry | null;
  accent: string;
  empty: string;
}) {
  if (!entry) return <span className="muted" style={{ fontSize: "0.86rem" }}>{empty}</span>;
  return (
    <div className="row spread" style={{ gap: 8, alignItems: "baseline" }}>
      <span className="muted" style={{ fontSize: "0.82rem" }}>
        {entry.detail}
      </span>
      <strong style={{ color: accent, fontVariantNumeric: "tabular-nums" }}>
        {entry.score}
      </strong>
    </div>
  );
}

function formatWhen(ms: number): string {
  return new Intl.DateTimeFormat("ro-RO", {
    day: "2-digit",
    month: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(ms));
}
