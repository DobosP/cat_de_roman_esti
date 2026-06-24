// ResultCard — the shared end-of-game card used by every word game so winning, losing,
// the score read-out, the "Record!" celebration, and the share/copy + replay actions all
// look and behave identically across the arcade.
//
// It is presentational only: the host owns the game state and passes in the copy handler,
// the replay handler, and onExit. Honours prefers-reduced-motion via framer's MotionConfig
// (set arcade-wide in App.tsx) so the pop-in is skipped when requested.

import type { ReactNode } from "react";
import { motion } from "framer-motion";

export function ResultCard({
  icon,
  title,
  accent,
  won = true,
  children,
  score,
  scoreLabel = "SCOR",
  isRecord = false,
  isPuzzleRecord = false,
  shareText,
  onCopy,
  onReplay,
  onExit,
  replayLabel = "Joc nou →",
}: {
  /** Big celebratory glyph. */
  icon: ReactNode;
  /** Headline (e.g. "Ai craftat tinta!"). */
  title: ReactNode;
  /** Game accent colour for the border glow + score number. */
  accent: string;
  /** Win vs. loss styling (loss drops the glow). */
  won?: boolean;
  /** Free-form body (recap line, target reveal, …). */
  children?: ReactNode;
  /** Numeric score to feature; omit to hide the score block. */
  score?: number;
  scoreLabel?: string;
  /** Show the personal-best celebration badge. */
  isRecord?: boolean;
  /** Show that this run is the local best for this exact puzzle. */
  isPuzzleRecord?: boolean;
  /** When present (and onCopy given), renders a "Copiaza rezultatul" button. */
  shareText?: string | null;
  onCopy?: () => void;
  /** Start a fresh game. */
  onReplay?: () => void;
  /** Return to the arcade. */
  onExit?: () => void;
  replayLabel?: string;
}) {
  const ring = won ? accent : "var(--surface-border-strong)";
  return (
    <motion.div
      className="card center col"
      initial={{ scale: 0.88, opacity: 0 }}
      animate={{ scale: 1, opacity: 1 }}
      transition={{ type: "spring", stiffness: 240, damping: 18 }}
      role="status"
      aria-live="polite"
      style={{
        gap: 10,
        padding: 24,
        textAlign: "center",
        borderColor: ring,
        boxShadow: won ? `0 0 60px -18px ${accent}` : "var(--shadow-pop)",
      }}
    >
      <div style={{ fontSize: "2.4rem", lineHeight: 1 }} aria-hidden>
        {icon}
      </div>
      <h2 style={{ margin: "2px 0", color: won ? accent : "var(--text)" }}>{title}</h2>

      {children && (
        <div className="muted" style={{ margin: 0, fontSize: "0.95rem" }}>
          {children}
        </div>
      )}

      {score !== undefined && (
        <div className="col center" style={{ gap: 4, marginTop: 4 }}>
          <span className="faint" style={{ fontSize: "0.72rem", letterSpacing: "0.08em" }}>
            {scoreLabel}
          </span>
          <div
            style={{
              fontFamily: "var(--font-display)",
              fontWeight: 800,
              fontSize: "2rem",
              color: won ? accent : "var(--text)",
              fontVariantNumeric: "tabular-nums",
            }}
          >
            {score}
          </div>
          {isRecord && (
            <motion.span
              className="badge"
              initial={{ scale: 0.6, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              transition={{ type: "spring", stiffness: 300, damping: 16 }}
              style={{ borderColor: "var(--warn)", color: "var(--warn)", fontWeight: 800 }}
            >
              ★ Record!
            </motion.span>
          )}
          {!isRecord && isPuzzleRecord && (
            <motion.span
              className="badge"
              initial={{ scale: 0.6, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              transition={{ type: "spring", stiffness: 300, damping: 16 }}
              style={{ borderColor: "var(--good)", color: "var(--good)", fontWeight: 800 }}
            >
              ★ Record puzzle
            </motion.span>
          )}
        </div>
      )}

      <div className="row center wrap" style={{ gap: 12, marginTop: 12 }}>
        {shareText && onCopy && (
          <button type="button" className="btn btn-primary" onClick={onCopy}>
            <span aria-hidden>📋</span> Copiaza rezultatul
          </button>
        )}
        {onReplay && (
          <button type="button" className="btn btn-ghost" onClick={onReplay}>
            {replayLabel}
          </button>
        )}
        {onExit && (
          <button type="button" className="btn btn-ghost" onClick={onExit}>
            Meniu
          </button>
        )}
      </div>
    </motion.div>
  );
}
