import { Csp } from "./CspStyle";
// GameIntro — the shared "before you play" card: icon, title, tag, how-to,
// difficulty (passed as children), the primary start action and the daily
// challenge. All four games previously hand-rolled this with drifting styles.
//
// The start button takes initial focus, so Enter starts the game without any
// global key listener (which used to collide across screens). The entrance
// (opacity/translate/scale) is a CSS keyframe on .game-intro; reduced motion
// disables it through the stylesheet.

import type { ComponentChildren } from "preact";
import { useLayoutEffect, useRef } from "preact/hooks";
import { Badge, Button } from "@roedu/ui";
import { useDailyIntent } from "../hooks/useDailyIntent";
import type { ScoreEntry } from "../scores/core";
import { displayDetail } from "../share";
import { PlayGuide, type PlayGuideStep } from "./PlayGuide";
import { StartFailureNotice } from "./StartFailureNotice";

export interface ResumeRecoveryNotice {
  kind: "failed" | "changed";
  canRetry: boolean;
  onRetry: () => void;
}

export function GameIntro({
  icon,
  title,
  tag,
  accent,
  glow,
  description,
  steps,
  best,
  children,
  startLabel = "Începe →",
  onStart,
  onDaily,
  dailyLabel = "Provocarea zilei",
  starting = false,
  startFailed = false,
  resumeRecovery,
}: {
  icon: ComponentChildren;
  title: string;
  tag?: string;
  accent: string;
  glow?: string;
  /** How-to copy (free-form). */
  description: ComponentChildren;
  /** Three terse actions that teach the loop without a rules wall. */
  steps?: PlayGuideStep[];
  /** Personal best, if any (renders the record line). */
  best?: ScoreEntry | null;
  /** Difficulty picker + any game-specific extras. */
  children?: ComponentChildren;
  startLabel?: string;
  onStart: () => void;
  /** Renders the shared daily-challenge button when given. */
  onDaily?: () => void;
  dailyLabel?: string;
  /** Disables actions while the game is being created. */
  starting?: boolean;
  /** Keep a failed new-round request visible beside its existing retry actions. */
  startFailed?: boolean;
  /** Persistent recovery for a saved game that could not safely be adopted. */
  resumeRecovery?: ResumeRecoveryNotice | null;
}) {
  const intent = useDailyIntent();
  const primaryRef = useRef<HTMLButtonElement | null>(null);
  // Initial focus on mount only (the former autoFocus): a later intro mount in the
  // same document must focus again, which the HTML attribute does only once.
  useLayoutEffect(() => { primaryRef.current?.focus(); }, []);
  // The circuit carries intent only. A saved round still resumes normally and
  // creating a daily round always requires the player's explicit start action,
  // which also uses up the intent so a later return here leads with free play.
  const dailyFirst = Boolean(onDaily) && intent.active;
  const consumeThen = (action?: () => void) => () => {
    intent.consume();
    action?.();
  };
  return (
    <Csp.div
      className="card game-intro game-intro-enter"
      inert={starting}
      aria-busy={starting}
      css={{
        boxShadow: glow ? `0 0 80px -30px ${glow}, var(--shadow-card)` : undefined,
      }}
    >
      <Csp.div
        className="game-intro-icon"
        aria-hidden
        css={{ background: `${accent}22`, borderColor: `${accent}55` }}
      >
        {icon}
      </Csp.div>
      <div className="col center">
        <Csp.h2 className="game-intro-title" css={{ color: accent }}>{title}</Csp.h2>
        {tag && (
          <Badge color={accent} size="sm">
            {tag}
          </Badge>
        )}
      </div>
      <div className="muted game-intro-description">{description}</div>
      {steps && <PlayGuide steps={steps} />}

      {children && <div className="col game-intro-extras">{children}</div>}

      {resumeRecovery && (
        <div className="card col game-intro-recovery" role="alert">
          <strong>
            {resumeRecovery.kind === "failed"
              ? "Nu am putut relua jocul salvat. Nu l-am șters."
              : "Jocul salvat s-a schimbat în altă filă."}
          </strong>
          {resumeRecovery.canRetry && (
            <Button variant="secondary" onClick={resumeRecovery.onRetry} disabled={starting}>
              {resumeRecovery.kind === "failed"
                ? "Reîncearcă reluarea"
                : "Încarcă jocul curent"}
            </Button>
          )}
        </div>
      )}

      <StartFailureNotice failed={startFailed} />
      <div className="row center wrap game-intro-actions">
        <Button ref={primaryRef} onClick={consumeThen(dailyFirst ? onDaily : onStart)} disabled={starting} size="lg">
          {dailyFirst ? "Joacă provocarea zilei" : startLabel}
        </Button>
        {onDaily && (
          <Button
            variant="secondary"
            onClick={consumeThen(dailyFirst ? onStart : onDaily)}
            disabled={starting}
            title={dailyFirst ? "Un joc nou, în afara circuitului zilnic." : "Provocare zilnică. Categoria se aplică doar jocurilor libere."}
          >
            {!dailyFirst && <span aria-hidden>📅</span>} {dailyFirst ? "Joacă liber" : dailyLabel}
          </Button>
        )}
      </div>

      {best && (
        <p className="faint game-intro-best">
          Recordul tău: <Csp.strong css={{ color: accent }}>{best.score}</Csp.strong> · {displayDetail(best.detail)}
        </p>
      )}
    </Csp.div>
  );
}
