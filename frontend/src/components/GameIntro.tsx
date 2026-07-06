// GameIntro — the shared "before you play" card: icon, title, tag, how-to,
// difficulty (passed as children), the primary start action and the daily
// challenge. All four games previously hand-rolled this with drifting styles.
//
// The start button takes initial focus, so Enter starts the game without any
// global key listener (which used to collide across screens).

import type { ReactNode } from "react";
import { motion } from "framer-motion";
import { Badge, Button } from "@roedu/ui";
import type { ScoreEntry } from "../scores";

export function GameIntro({
  icon,
  title,
  tag,
  accent,
  glow,
  description,
  best,
  children,
  startLabel = "Incepe →",
  onStart,
  onDaily,
  dailyLabel = "Provocarea zilei",
  starting = false,
}: {
  icon: ReactNode;
  title: string;
  tag?: string;
  accent: string;
  glow?: string;
  /** How-to copy (free-form). */
  description: ReactNode;
  /** Personal best, if any (renders the record line). */
  best?: ScoreEntry | null;
  /** Difficulty picker + any game-specific extras. */
  children?: ReactNode;
  startLabel?: string;
  onStart: () => void;
  /** Renders the shared daily-challenge button when given. */
  onDaily?: () => void;
  dailyLabel?: string;
  /** Disables actions while the game is being created. */
  starting?: boolean;
}) {
  return (
    <motion.div
      className="card game-intro"
      initial={{ opacity: 0, y: 18, scale: 0.98 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      transition={{ duration: 0.45, ease: [0.22, 1, 0.36, 1] }}
      style={{
        boxShadow: glow ? `0 0 80px -30px ${glow}, var(--shadow-card)` : undefined,
      }}
    >
      <div
        className="game-intro-icon"
        aria-hidden
        style={{ background: `${accent}22`, borderColor: `${accent}55` }}
      >
        {icon}
      </div>
      <div className="col center" style={{ gap: 6 }}>
        <h2 style={{ color: accent, fontSize: "1.7rem" }}>{title}</h2>
        {tag && (
          <Badge color={accent} size="sm">
            {tag}
          </Badge>
        )}
      </div>
      <div className="muted game-intro-description">{description}</div>

      {children && <div className="col game-intro-extras">{children}</div>}

      <div className="row center wrap" style={{ gap: 12, marginTop: 6 }}>
        <Button autoFocus onClick={onStart} disabled={starting} size="lg">
          {startLabel}
        </Button>
        {onDaily && (
          <Button
            variant="secondary"
            onClick={onDaily}
            disabled={starting}
            title="Acelasi puzzle pentru toata lumea, azi"
          >
            <span aria-hidden>📅</span> {dailyLabel}
          </Button>
        )}
      </div>

      {best && (
        <p className="faint" style={{ margin: 0, fontSize: "0.82rem" }}>
          Recordul tau: <strong style={{ color: accent }}>{best.score}</strong> · {best.detail}
        </p>
      )}
    </motion.div>
  );
}
