import type { ComponentChildren } from "preact";
import { useId, useLayoutEffect, useRef } from "preact/hooks";
import { roNoun } from "../share";

export function ResultCard({ title, children, steps, perfect, podium, onCopy, onReplay, onExit, actionsBusy }: {
  title: ComponentChildren;
  children?: ComponentChildren;
  steps?: number;
  perfect?: boolean;
  podium?: ComponentChildren;
  onCopy?: () => void;
  onReplay: () => void;
  onExit: () => void;
  actionsBusy?: boolean;
}) {
  const heading = useRef<HTMLHeadingElement>(null);
  const titleId = useId();
  useLayoutEffect(() => { heading.current?.focus(); }, []);
  return (
    <section className="card game-result" aria-labelledby={titleId}>
      <h2 id={titleId} ref={heading} tabIndex={-1}>{title}</h2>
      {children}
      {perfect && <strong className="game-result-perfect">Perfect</strong>}
      {steps !== undefined && <p>Pașii tăi: <strong>{steps} {roNoun(steps, "pas", "pași")}</strong></p>}
      {podium}
      <div className="game-result-actions">
        <button type="button" className="btn" onClick={onReplay} disabled={actionsBusy}>Încă o rundă</button>
        <button type="button" className="btn game-result-secondary" onClick={onExit}>Înapoi la jocuri</button>
        {onCopy && <button type="button" className="btn game-result-secondary" onClick={onCopy}>Copiază rezultatul</button>}
      </div>
    </section>
  );
}
