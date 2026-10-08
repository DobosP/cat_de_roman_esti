import type { CSSProperties, ReactNode } from "react";

export interface PlayGuideStep {
  icon: ReactNode;
  label: string;
}

export function PlayGuide({
  steps,
  label = "Cum joci",
}: {
  steps: PlayGuideStep[];
  label?: string;
}) {
  return (
    <ol className="play-guide" aria-label={label}>
      {steps.map((step, index) => (
        <li className="play-guide-step" key={`${index}-${step.label}`}>
          <span className="play-guide-count" aria-hidden>
            {index + 1}
          </span>
          <span className="play-guide-icon" aria-hidden>
            {step.icon}
          </span>
          <strong>{step.label}</strong>
        </li>
      ))}
    </ol>
  );
}

export function NextMove({
  icon,
  title,
  detail,
  progress,
  accent,
  ready = false,
  announce = true,
  action,
  className,
}: {
  icon: ReactNode;
  title: string;
  detail?: string;
  progress?: string;
  accent: string;
  ready?: boolean;
  announce?: boolean;
  action?: ReactNode;
  className?: string;
}) {
  return (
    <div
      className={`next-move${ready ? " next-move--ready" : ""}${className ? ` ${className}` : ""}`}
      style={{ "--cue-accent": accent } as CSSProperties}
    >
      <span className="next-move-icon" aria-hidden>
        {icon}
      </span>
      <span
        className="next-move-copy"
        role={announce ? "status" : undefined}
        aria-live={announce ? "polite" : undefined}
        aria-atomic={announce ? "true" : undefined}
      >
        <span className="next-move-label">ACUM</span>
        <strong>{title}</strong>
        {detail && <span className="muted">{detail}</span>}
      </span>
      {progress && <span className="next-move-progress">{progress}</span>}
      {action && <span className="next-move-action">{action}</span>}
    </div>
  );
}
