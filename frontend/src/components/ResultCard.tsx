import { Csp, CspMotion } from "./CspStyle";
// ResultCard — the shared end-of-game card used by every word game so winning, losing,
// the score read-out, the "Record!" celebration, and the share/copy + replay actions all
// look and behave identically across the arcade. Wins get a confetti burst (skipped
// under reduced motion).
//
// It is presentational only: the host owns the game state and passes in the copy handler,
// the replay handler, and onExit.

import type { ReactNode } from "react";
import { m } from "framer-motion";
import { Badge, Button } from "@roedu/ui";
import { Confetti } from "./Confetti";
import { StartFailureNotice } from "./StartFailureNotice";

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
  onOptions,
  onExit,
  replayLabel = "Încă unul →",
  optionsLabel = "Schimbă opțiunile",
  actionsBusy = false,
  startFailed = false,
}: {
  /** Big celebratory glyph. */
  icon: ReactNode;
  /** Headline (e.g. "Ai făurit ținta!"). */
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
  /** When present (and onCopy given), renders a "Copiază rezultatul" button. */
  shareText?: string | null;
  onCopy?: () => void;
  /** Start a fresh game. */
  onReplay?: () => void;
  /** Return to the setup screen without leaving the game. */
  onOptions?: () => void;
  /** Return to the arcade. */
  onExit?: () => void;
  replayLabel?: string;
  optionsLabel?: string;
  /** Disable result actions while a replay/create request is in flight. */
  actionsBusy?: boolean;
  /** Persistent failed replay feedback, beside the action that can retry it. */
  startFailed?: boolean;
}) {
  const ring = won ? accent : "var(--surface-border-strong)";
  return (
    <CspMotion.div
      className="card center col"
      initial={{ scale: 0.88, opacity: 0 }}
      animate={{ scale: 1, opacity: 1 }}
      transition={{ type: "spring", stiffness: 240, damping: 18 }}
      role="status"
      aria-live="polite"
      css={{
        gap: "10px",
        padding: "24px",
        textAlign: "center",
        position: "relative",
        overflow: "hidden",
        borderColor: ring,
        boxShadow: won ? `0 0 60px -18px ${accent}` : "var(--shadow-pop)",
      }}
    >
      {won && <Confetti accent={accent} />}
      <CspMotion.div
        css={{ fontSize: "2.6rem", lineHeight: 1 }}
        aria-hidden
        initial={{ scale: 0.4, rotate: won ? -14 : 0 }}
        animate={{ scale: 1, rotate: 0 }}
        transition={{ type: "spring", stiffness: 260, damping: 14, delay: 0.08 }}
      >
        {icon}
      </CspMotion.div>
      <Csp.h2 css={{ margin: "2px 0", color: won ? accent : "var(--text)" }}>{title}</Csp.h2>

      {children && (
        <Csp.div className="muted" css={{ margin: "0px", fontSize: "0.95rem" }}>
          {children}
        </Csp.div>
      )}

      {score !== undefined && (
        <Csp.div className="col center" css={{ gap: "4px", marginTop: "4px" }}>
          <Csp.span className="faint" css={{ fontSize: "0.72rem", letterSpacing: "0.08em" }}>
            {scoreLabel}
          </Csp.span>
          <CspMotion.div
            initial={{ scale: 0.7 }}
            animate={{ scale: 1 }}
            transition={{ type: "spring", stiffness: 300, damping: 15, delay: 0.15 }}
            css={{
              fontFamily: "var(--font-display)",
              fontWeight: 700,
              fontSize: "2.2rem",
              color: won ? accent : "var(--text)",
              fontVariantNumeric: "tabular-nums",
            }}
          >
            {score}
          </CspMotion.div>
          {isRecord && (
            <m.span
              initial={{ scale: 0.6, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              transition={{ type: "spring", stiffness: 300, damping: 16, delay: 0.25 }}
            >
              <Badge color="var(--warn)">★ Record!</Badge>
            </m.span>
          )}
          {!isRecord && isPuzzleRecord && (
            <m.span
              initial={{ scale: 0.6, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              transition={{ type: "spring", stiffness: 300, damping: 16, delay: 0.25 }}
            >
              <Badge tone="success">★ Recordul acestei provocări</Badge>
            </m.span>
          )}
        </Csp.div>
      )}

      <StartFailureNotice failed={startFailed} reserveSpace={Boolean(onReplay)} />
      <Csp.div className="row center wrap" css={{ gap: "12px", marginTop: "12px", position: "relative" }}>
        {onReplay && (
          <Button onClick={onReplay} disabled={actionsBusy}>
            {actionsBusy ? "Se pregătește…" : replayLabel}
          </Button>
        )}
        {shareText && onCopy && (
          <Button variant="secondary" onClick={onCopy} disabled={actionsBusy}>
            <span aria-hidden>📋</span> Copiază rezultatul
          </Button>
        )}
        {onOptions && (
          <Button variant="secondary" onClick={onOptions} disabled={actionsBusy}>
            {optionsLabel}
          </Button>
        )}
        {onExit && (
          <Button variant="secondary" onClick={onExit} disabled={actionsBusy}>
            Meniu
          </Button>
        )}
      </Csp.div>
    </CspMotion.div>
  );
}
