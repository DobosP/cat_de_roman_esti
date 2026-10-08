import { Csp } from "./CspStyle";
// GameIntro — the shared "before you play" card: icon, title, tag, how-to,
// difficulty (passed as children), the primary start action and the daily
// challenge. All four games previously hand-rolled this with drifting styles.
//
// The start button takes initial focus, so Enter starts the game without any
// global key listener (which used to collide across screens).

import type { ReactNode } from "react";
import { CspMotion } from "./CspStyle";
import { Badge, Button } from "@roedu/ui";
import { useDailyIntent } from "../hooks/useDailyIntent";
import type { ScoreEntry } from "../scores";
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
  icon: ReactNode;
  title: string;
  tag?: string;
  accent: string;
  glow?: string;
  /** How-to copy (free-form). */
  description: ReactNode;
  /** Three terse actions that teach the loop without a rules wall. */
  steps?: PlayGuideStep[];
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
  /** Keep a failed new-round request visible beside its existing retry actions. */
  startFailed?: boolean;
  /** Persistent recovery for a saved game that could not safely be adopted. */
  resumeRecovery?: ResumeRecoveryNotice | null;
}) {
  const intent = useDailyIntent();
  // The circuit carries intent only. A saved round still resumes normally and
  // creating a daily round always requires the player's explicit start action,
  // which also uses up the intent so a later return here leads with free play.
  const dailyFirst = Boolean(onDaily) && intent.active;
  const consumeThen = (action?: () => void) => () => {
    intent.consume();
    action?.();
  };
  return (
    <CspMotion.div
      className="card game-intro"
      inert={starting}
      aria-busy={starting}
      initial={{ opacity: 0, y: 18, scale: 0.98 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      transition={{ duration: 0.45, ease: [0.22, 1, 0.36, 1] }}
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
      <Csp.div className="col center" css={{ gap: "6px" }}>
        <Csp.h2 css={{ color: accent, fontSize: "1.7rem" }}>{title}</Csp.h2>
        {tag && (
          <Badge color={accent} size="sm">
            {tag}
          </Badge>
        )}
      </Csp.div>
      <div className="muted game-intro-description">{description}</div>
      {steps && <PlayGuide steps={steps} />}

      {children && <div className="col game-intro-extras">{children}</div>}

      {resumeRecovery && (
        <Csp.div className="card col" role="alert" css={{ gap: "10px", padding: "14px", width: "100%" }}>
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
        </Csp.div>
      )}

      <StartFailureNotice failed={startFailed} />
      <Csp.div className="row center wrap game-intro-actions" css={{ gap: "12px", marginTop: "6px" }}>
        <Button autoFocus onClick={consumeThen(dailyFirst ? onDaily : onStart)} disabled={starting} size="lg">
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
      </Csp.div>

      {best && (
        <Csp.p className="faint" css={{ margin: "0px", fontSize: "0.82rem" }}>
          Recordul tău: <Csp.strong css={{ color: accent }}>{best.score}</Csp.strong> · {displayDetail(best.detail)}
        </Csp.p>
      )}
    </CspMotion.div>
  );
}
