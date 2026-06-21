import { useEffect, useMemo, useState } from "react";
import { motion } from "framer-motion";
import type { GameState } from "../api/types";
import { api, ApiError } from "../api/client";
import { categoryColor, categoryLabel } from "../theme/tokens";
import type { ToastKind } from "../components/Toast";
import { sound } from "../sound";

// Win screen: a framer-motion confetti burst, a score count-up, and Replay / Next.
// Replay restarts the SAME puzzle (server reset); Next starts a fresh puzzle of the
// same category + mode.

const CONFETTI_COLORS = [
  "#ffd166",
  "#5fd99b",
  "#8ec5ff",
  "#f178b6",
  "#c08bff",
  "#56d4dd",
];

function useCountUp(target: number, durationMs = 1100): number {
  const [value, setValue] = useState(0);
  useEffect(() => {
    let raf = 0;
    const start = performance.now();
    const tick = (now: number) => {
      const t = Math.min(1, (now - start) / durationMs);
      // easeOutCubic
      const eased = 1 - Math.pow(1 - t, 3);
      setValue(Math.round(target * eased));
      if (t < 1) raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [target, durationMs]);
  return value;
}

function ConfettiBurst() {
  const pieces = useMemo(
    () =>
      Array.from({ length: 64 }, (_, i) => {
        const angle = (Math.PI * 2 * i) / 64 + Math.random() * 0.4;
        const dist = 160 + Math.random() * 320;
        return {
          id: i,
          x: Math.cos(angle) * dist,
          y: Math.sin(angle) * dist - 120,
          rot: Math.random() * 720 - 360,
          color: CONFETTI_COLORS[i % CONFETTI_COLORS.length],
          delay: Math.random() * 0.18,
          size: 6 + Math.random() * 8,
        };
      }),
    [],
  );

  return (
    <div
      aria-hidden
      style={{
        position: "absolute",
        inset: 0,
        overflow: "hidden",
        pointerEvents: "none",
      }}
    >
      {pieces.map((p) => (
        <motion.span
          key={p.id}
          initial={{ x: 0, y: 0, opacity: 1, rotate: 0, scale: 1 }}
          animate={{
            x: p.x,
            y: p.y + 380,
            opacity: 0,
            rotate: p.rot,
            scale: 0.6,
          }}
          transition={{
            duration: 1.6 + Math.random() * 0.8,
            delay: p.delay,
            ease: [0.2, 0.7, 0.3, 1],
          }}
          style={{
            position: "absolute",
            left: "50%",
            top: "38%",
            width: p.size,
            height: p.size * 0.5,
            borderRadius: 2,
            background: p.color,
            boxShadow: `0 0 8px ${p.color}`,
          }}
        />
      ))}
    </div>
  );
}

export function Win({
  game,
  onReplay,
  onMenu,
  onToast,
}: {
  game: GameState;
  onReplay: (game: GameState) => void;
  onMenu: () => void;
  onToast: (message: string, kind?: ToastKind) => void;
}) {
  const score = useCountUp(game.score);
  const [busy, setBusy] = useState<"replay" | "next" | null>(null);
  const catColor = categoryColor(game.category);
  const perfect = game.hops <= game.puzzle.par;

  // Triumphant rising arpeggio when the Win screen mounts (once per win).
  useEffect(() => {
    sound.playWin();
  }, []);

  async function handleReplay() {
    setBusy("replay");
    try {
      const fresh = await api.resetGame(game.game_id);
      onReplay(fresh);
    } catch (err) {
      onToast(
        err instanceof ApiError
          ? `Nu am putut relua (${err.status}).`
          : "Nu am putut relua jocul.",
        "error",
      );
      setBusy(null);
    }
  }

  async function handleNext() {
    setBusy("next");
    try {
      // Pass the just-finished puzzle id as exclude so Next advances to a
      // DIFFERENT puzzle when one exists (Replay keeps the same puzzle).
      const fresh = await api.createGame(
        game.category,
        game.mode,
        game.puzzle.id,
      );
      onReplay(fresh);
    } catch (err) {
      onToast(
        err instanceof ApiError
          ? err.status === 404
            ? "Nu mai exista alta enigma aici."
            : `Nu am putut porni urmatoarea (${err.status}).`
          : "Nu am putut porni urmatoarea enigma.",
        "error",
      );
      setBusy(null);
    }
  }

  return (
    <div
      className="screen-pad fill center"
      style={{ position: "relative", display: "flex" }}
    >
      <ConfettiBurst />
      <motion.div
        className="card"
        initial={{ scale: 0.85, opacity: 0, y: 20 }}
        animate={{ scale: 1, opacity: 1, y: 0 }}
        transition={{ type: "spring", stiffness: 220, damping: 20 }}
        style={{
          position: "relative",
          padding: "clamp(24px, 5vw, 48px)",
          width: "min(520px, 100%)",
          textAlign: "center",
          display: "grid",
          gap: 18,
          borderColor: catColor,
          boxShadow: `0 0 60px -18px ${catColor}, var(--shadow-pop)`,
        }}
      >
        <motion.div
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          transition={{ delay: 0.1, type: "spring", stiffness: 300, damping: 14 }}
          style={{ fontSize: "3rem" }}
          aria-hidden
        >
          {perfect ? "★" : "✦"}
        </motion.div>

        <div className="col" style={{ gap: 6 }}>
          <h1 style={{ fontSize: "clamp(1.8rem, 5vw, 2.6rem)" }}>
            {perfect ? "Perfect!" : "Ai reusit!"}
          </h1>
          <p className="muted" style={{ margin: 0 }}>
            Ai ajuns la tinta in{" "}
            <strong style={{ color: "var(--text)" }}>{game.hops}</strong>{" "}
            salturi (par {game.puzzle.par}).
          </p>
        </div>

        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.25 }}
          style={{
            fontFamily: "var(--font-display)",
            fontWeight: 800,
            fontSize: "clamp(2.6rem, 9vw, 4rem)",
            fontVariantNumeric: "tabular-nums",
            color: "var(--warn)",
            textShadow: "0 0 30px rgba(255,209,102,0.4)",
            lineHeight: 1,
          }}
        >
          {score}
          <span
            style={{
              fontSize: "1rem",
              color: "var(--text-dim)",
              marginLeft: 8,
              fontWeight: 600,
            }}
          >
            puncte
          </span>
        </motion.div>

        <div
          className="row center wrap"
          style={{ gap: 8, color: "var(--text-dim)", fontSize: "0.85rem" }}
        >
          <span className="badge" style={{ borderColor: catColor, color: catColor }}>
            {categoryLabel(game.category)}
          </span>
          <span className="badge">{game.mode === "hard" ? "Greu" : "Usor"}</span>
        </div>

        <div className="row center wrap" style={{ gap: 12, marginTop: 6 }}>
          <button
            type="button"
            className="btn btn-ghost"
            disabled={busy !== null}
            onClick={handleReplay}
          >
            {busy === "replay" ? "…" : "↻ Reia"}
          </button>
          <button
            type="button"
            className="btn btn-primary"
            disabled={busy !== null}
            onClick={handleNext}
          >
            {busy === "next" ? "…" : "Urmatoarea →"}
          </button>
          <button
            type="button"
            className="btn btn-ghost"
            disabled={busy !== null}
            onClick={onMenu}
          >
            Meniu
          </button>
        </div>
      </motion.div>
    </div>
  );
}
