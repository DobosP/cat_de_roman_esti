import { Csp } from "./CspStyle";
// ResultCard — the shared end-of-game card used by every word game so winning, losing,
// the score read-out, the "Record!" celebration, and the share/copy + replay actions all
// look and behave identically across the arcade. Wins get a confetti burst (skipped
// under reduced motion by the kit).
//
// It is presentational only: the host owns the game state and passes in the copy handler,
// the replay handler, and onExit. The former Framer springs are CSS keyframes
// (result-*-enter classes); reduced motion disables them through the stylesheet.

import type { ComponentChildren } from "preact";
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
  icon: ComponentChildren;
  /** Headline (e.g. "Ai făurit ținta!"). */
  title: ComponentChildren;
  /** Game accent colour for the border glow + score number. */
  accent: string;
  /** Win vs. loss styling (loss drops the glow + confetti). */
  won?: boolean;
  /** Free-form body (recap line, target reveal, …). */
  children?: ComponentChildren;
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
    <Csp.div
      className="card center col result-card-enter"
      role="status"
      aria-live="polite"
      css={{
        borderColor: ring,
        boxShadow: won ? `0 0 60px -18px ${accent}` : "var(--shadow-pop)",
      }}
    >
      {won && <Confetti />}
      <div
        aria-hidden
        className={won ? "result-icon-enter result-icon-enter--won" : "result-icon-enter"}
      >
        {icon}
      </div>
      <Csp.h2 className="result-card-title" css={{ color: won ? accent : "var(--text)" }}>{title}</Csp.h2>

      {children && (
        <div className="muted result-card-detail">
          {children}
        </div>
      )}

      {score !== undefined && (
        <div className="col center result-card-score">
          <span className="faint result-card-score-label">
            {scoreLabel}
          </span>
          <Csp.div
            className="result-score-enter"
            css={{
              color: won ? accent : "var(--text)",
            }}
          >
            {score}
          </Csp.div>
          {isRecord && (
            <span className="result-record-enter">
              <Badge color="var(--warn)">★ Record!</Badge>
            </span>
          )}
          {!isRecord && isPuzzleRecord && (
            <span className="result-record-enter">
              <Badge tone="success">★ Recordul acestei provocări</Badge>
            </span>
          )}
        </div>
      )}

      <StartFailureNotice failed={startFailed} reserveSpace={Boolean(onReplay)} />
      <div className="row center wrap result-card-actions">
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
      </div>
    </Csp.div>
  );
}
