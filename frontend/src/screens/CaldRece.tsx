// CaldRece — "Cald sau Rece" (Contexto/Semantle-style) screen.
//
// A hidden secret concept lives on the server. The player types concept guesses; each
// guess comes back with a graph DISTANCE, a temperature tier, and a 0..100 closeness.
// The server is the only source of truth (it holds the secret + sorts the guess list
// best-first); this component only renders what it returns and surfaces errors as toasts.

import { useCallback, useEffect, useRef, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import type { ToastKind } from "../components/Toast";
import { sound } from "../sound";
import {
  contextoApi,
  ApiError,
  type ContextoState,
  type Guess,
  type GuessResult,
  type Temperature,
} from "../api/contexto";

// Temperature -> colour on a hot/cold gradient (hot = red/orange, cold = blue).
const TEMP_COLOR: Record<Temperature, string> = {
  Gasit: "#5fd99b",
  Fierbinte: "#ff5d3b",
  Cald: "#f4a259",
  Caldut: "#ffd166",
  Rece: "#8ec5ff",
  Inghetat: "#7bb8f2",
};

const TEMP_ICON: Record<Temperature, string> = {
  Gasit: "🎯",
  Fierbinte: "🔥",
  Cald: "♨️",
  Caldut: "🌤️",
  Rece: "❄️",
  Inghetat: "🧊",
};

/** Blend the colour by closeness so the bar reads hot→cold within a tier too. */
function barColor(g: Guess): string {
  return TEMP_COLOR[g.temperature] ?? "#9aa3b2";
}

function GuessRow({ g, isLatest }: { g: Guess; isLatest: boolean }) {
  const color = barColor(g);
  const pct = Math.max(2, Math.min(100, g.closeness));
  return (
    <motion.div
      layout
      initial={isLatest ? { opacity: 0, y: -10, scale: 0.97 } : false}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      transition={{ type: "spring", stiffness: 380, damping: 28 }}
      className="card"
      style={{
        position: "relative",
        overflow: "hidden",
        padding: "10px 14px",
        display: "grid",
        gap: 8,
        borderColor: isLatest ? color : "var(--border)",
        boxShadow: isLatest ? `0 0 22px -10px ${color}` : undefined,
      }}
    >
      {/* hot/cold fill bar */}
      <div
        aria-hidden
        style={{
          position: "absolute",
          inset: 0,
          width: `${pct}%`,
          background: `linear-gradient(90deg, ${color}26, ${color}0d)`,
          transition: "width 0.5s cubic-bezier(0.2,0.7,0.3,1)",
        }}
      />
      <div
        className="row spread"
        style={{ position: "relative", gap: 10, alignItems: "center" }}
      >
        <span className="row" style={{ gap: 8, alignItems: "center" }}>
          <span aria-hidden style={{ fontSize: "1.1rem" }}>
            {TEMP_ICON[g.temperature]}
          </span>
          <strong style={{ fontSize: "0.98rem" }}>{g.label}</strong>
        </span>
        <span className="row" style={{ gap: 8, alignItems: "center" }}>
          <span
            className="badge"
            style={{ borderColor: color, color, fontWeight: 700 }}
          >
            {g.temperature}
          </span>
          <span
            className="muted"
            style={{
              fontVariantNumeric: "tabular-nums",
              fontSize: "0.82rem",
              minWidth: 38,
              textAlign: "right",
            }}
            title={`Distanta ${g.distance} salturi`}
          >
            {g.closeness}
          </span>
        </span>
      </div>
    </motion.div>
  );
}

export default function CaldRece({
  onExit,
  onToast,
}: {
  onExit: () => void;
  onToast: (message: string, kind?: ToastKind) => void;
}) {
  const [state, setState] = useState<ContextoState | null>(null);
  const [text, setText] = useState("");
  const [busy, setBusy] = useState(false);
  const [latestId, setLatestId] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  // Guard StrictMode's double mount from creating two games.
  const started = useRef(false);

  const start = useCallback(async () => {
    setBusy(true);
    try {
      const fresh = await contextoApi.createGame();
      setState(fresh);
      setLatestId(null);
      setText("");
      inputRef.current?.focus();
    } catch (err) {
      onToast(
        err instanceof ApiError
          ? `Nu am putut porni jocul (${err.status}).`
          : "Nu am putut porni jocul. Verifica serverul.",
        "error",
      );
    } finally {
      setBusy(false);
    }
  }, [onToast]);

  useEffect(() => {
    if (started.current) return;
    started.current = true;
    void start();
  }, [start]);

  const won = state?.won ?? false;
  const gaveUp = state?.gave_up ?? false;
  const finished = won || gaveUp;

  const handleGuess = useCallback(
    async (e?: React.FormEvent) => {
      e?.preventDefault();
      if (!state || busy || finished) return;
      const q = text.trim();
      if (!q) return;
      setBusy(true);
      try {
        const res: GuessResult = await contextoApi.submitGuess(
          state.game_id,
          q,
        );
        if (!res.ok) {
          sound.playError();
          onToast(res.message, "error");
          setState((prev) =>
            prev
              ? { ...prev, guesses: res.guesses, attempts: res.attempts }
              : prev,
          );
          return;
        }
        setText("");
        setLatestId(res.guess.id);
        setState((prev) =>
          prev
            ? {
                ...prev,
                guesses: res.guesses,
                attempts: res.attempts,
                won: res.won,
                target: res.target ?? prev.target,
              }
            : prev,
        );
        if (res.won) {
          sound.playWin();
        } else if (res.guess.temperature === "Fierbinte") {
          sound.playRecord();
        } else {
          sound.playHop();
        }
      } catch (err) {
        onToast(
          err instanceof ApiError
            ? `Ghicirea a esuat (${err.status}).`
            : "Ghicirea a esuat. Verifica serverul.",
          "error",
        );
      } finally {
        setBusy(false);
        inputRef.current?.focus();
      }
    },
    [state, busy, finished, text, onToast],
  );

  const handleGiveUp = useCallback(async () => {
    if (!state || busy || finished) return;
    setBusy(true);
    try {
      const res = await contextoApi.giveUp(state.game_id);
      sound.playUndo();
      setState(res);
    } catch (err) {
      onToast(
        err instanceof ApiError
          ? `Nu am putut renunta (${err.status}).`
          : "Nu am putut renunta.",
        "error",
      );
    } finally {
      setBusy(false);
    }
  }, [state, busy, finished, onToast]);

  const guesses = state?.guesses ?? [];
  const best = guesses[0];

  return (
    <div className="screen-pad fill" style={{ display: "flex" }}>
      <div
        className="container col fill"
        style={{ gap: 16, minHeight: 0, paddingBlock: 8 }}
      >
        {/* header */}
        <div className="row spread wrap" style={{ gap: 10 }}>
          <button
            type="button"
            className="btn btn-ghost"
            onClick={onExit}
            disabled={busy && !state}
          >
            ← Meniu
          </button>
          <div className="row" style={{ gap: 10, alignItems: "center" }}>
            <span
              className="badge"
              title="Incercari"
              style={{ fontVariantNumeric: "tabular-nums" }}
            >
              {state?.attempts ?? 0} incercari
            </span>
            <button
              type="button"
              className="btn btn-ghost"
              onClick={() => void handleGiveUp()}
              disabled={busy || finished || !state}
            >
              Renunta
            </button>
            <button
              type="button"
              className="btn btn-ghost"
              onClick={() => void start()}
              disabled={busy}
              title="Joc nou"
            >
              ↻ Nou
            </button>
          </div>
        </div>

        {/* intro / title */}
        <div className="col" style={{ gap: 4 }}>
          <h1 style={{ fontSize: "clamp(1.5rem, 4vw, 2.2rem)", margin: 0 }}>
            Cald sau Rece
          </h1>
          <p className="muted" style={{ margin: 0, fontSize: "0.9rem" }}>
            Exista un concept secret. Scrie ce-ti vine in minte — iti spun cat
            de aproape esti. 🔥 fierbinte … 🧊 inghetat.
          </p>
        </div>

        {/* input */}
        <form onSubmit={handleGuess} className="row" style={{ gap: 8 }}>
          <input
            ref={inputRef}
            className="card fill"
            style={{
              padding: "12px 14px",
              fontSize: "1rem",
              background: "var(--surface)",
              color: "var(--text)",
              outline: "none",
            }}
            placeholder={finished ? "Joc terminat" : "Scrie un concept…"}
            value={text}
            onChange={(e) => setText(e.target.value)}
            disabled={busy || finished}
            autoComplete="off"
            spellCheck={false}
            aria-label="Concept de ghicit"
          />
          <button
            type="submit"
            className="btn btn-primary"
            disabled={busy || finished || !text.trim()}
          >
            Ghiceste
          </button>
        </form>

        {/* win / giveup banner */}
        <AnimatePresence>
          {finished && state?.target && (
            <motion.div
              key="result"
              initial={{ opacity: 0, scale: 0.92, y: -8 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0 }}
              transition={{ type: "spring", stiffness: 260, damping: 20 }}
              className="card"
              style={{
                padding: "16px 18px",
                display: "grid",
                gap: 6,
                borderColor: won ? "var(--good)" : "var(--warn)",
                boxShadow: `0 0 40px -16px ${won ? "var(--good)" : "var(--warn)"}`,
                textAlign: "center",
              }}
            >
              <div style={{ fontSize: "2rem" }} aria-hidden>
                {won ? "🎯" : "🫥"}
              </div>
              <strong style={{ fontSize: "1.2rem" }}>
                {won ? "Ai gasit conceptul!" : "Conceptul secret era:"}
              </strong>
              <span style={{ fontSize: "1.4rem", color: "var(--text)" }}>
                {state.target.label}
              </span>
              {state.target.description && (
                <span className="muted" style={{ fontSize: "0.85rem" }}>
                  {state.target.description}
                </span>
              )}
              <div className="center" style={{ marginTop: 8 }}>
                <button
                  type="button"
                  className="btn btn-primary"
                  onClick={() => void start()}
                  disabled={busy}
                >
                  Joc nou →
                </button>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* best so far */}
        {!finished && best && (
          <p className="faint center" style={{ fontSize: "0.82rem", margin: 0 }}>
            Cel mai aproape:{" "}
            <strong style={{ color: barColor(best) }}>{best.label}</strong> (
            {best.closeness}/100)
          </p>
        )}

        {/* guess list (server-sorted best-first) */}
        <div
          className="col fill"
          style={{ gap: 8, overflowY: "auto", minHeight: 0, paddingRight: 4 }}
        >
          {guesses.length === 0 && !finished && (
            <p className="faint center" style={{ marginTop: 24 }}>
              Nicio incercare inca. Incepe cu orice idee!
            </p>
          )}
          <AnimatePresence initial={false}>
            {guesses.map((g) => (
              <GuessRow key={g.id} g={g} isLatest={g.id === latestId} />
            ))}
          </AnimatePresence>
        </div>
      </div>
    </div>
  );
}
