// ResultCard — the shared end-of-game card used by every word game so winning, losing,
// the score read-out, the "Record!" celebration, and the share/copy + replay actions all
// look and behave identically across the arcade. Wins get a confetti burst (skipped
// under reduced motion).
//
// It is presentational only: the host owns the game state and passes in the copy handler,
// the replay handler, and onExit.

import type { ReactNode } from "react";
import { motion } from "framer-motion";
import { Badge, Button } from "@roedu/ui";
import { Confetti } from "./Confetti";

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
  /** Win vs. loss styling (loss drops the glow + confetti). */
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
        position: "relative",
        overflow: "hidden",
        borderColor: ring,
        boxShadow: won ? `0 0 60px -18px ${accent}` : "var(--shadow-pop)",
      }}
    >
      {won && <Confetti accent={accent} />}
      <motion.div
        style={{ fontSize: "2.6rem", lineHeight: 1 }}
        aria-hidden
        initial={{ scale: 0.4, rotate: won ? -14 : 0 }}
        animate={{ scale: 1, rotate: 0 }}
        transition={{ type: "spring", stiffness: 260, damping: 14, delay: 0.08 }}
      >
        {icon}
      </motion.div>
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
          <motion.div
            initial={{ scale: 0.7 }}
            animate={{ scale: 1 }}
            transition={{ type: "spring", stiffness: 300, damping: 15, delay: 0.15 }}
            style={{
              fontFamily: "var(--font-display)",
              fontWeight: 700,
              fontSize: "2.2rem",
              color: won ? accent : "var(--text)",
              fontVariantNumeric: "tabular-nums",
            }}
          >
            {score}
          </motion.div>
          {isRecord && (
            <motion.span
              initial={{ scale: 0.6, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              transition={{ type: "spring", stiffness: 300, damping: 16, delay: 0.25 }}
            >
              <Badge color="var(--warn)">★ Record!</Badge>
            </motion.span>
          )}
          {!isRecord && isPuzzleRecord && (
            <motion.span
              initial={{ scale: 0.6, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              transition={{ type: "spring", stiffness: 300, damping: 16, delay: 0.25 }}
            >
              <Badge tone="success">★ Record puzzle</Badge>
            </motion.span>
          )}
        </div>
      )}

      <div className="row center wrap" style={{ gap: 12, marginTop: 12, position: "relative" }}>
        {shareText && onCopy && (
          <Button onClick={onCopy}>
            <span aria-hidden>📋</span> Copiaza rezultatul
          </Button>
        )}
        {onReplay && (
          <Button variant="secondary" onClick={onReplay}>
            {replayLabel}
          </Button>
        )}
        {onExit && (
          <Button variant="secondary" onClick={onExit}>
            Meniu
          </Button>
        )}
      </div>
    </motion.div>
  );
}
