import type { ComponentChildren } from "preact";
import { useId, useLayoutEffect, useRef, useState } from "preact/hooks";
import type { GameHelpCopy } from "../gameHelp.mjs";
import type { GameDef } from "../games";
import type { ResumeRecovery } from "../hooks/useSavedGameResume";

export function GameFrame({ game, mode, onExit, help, options, tools, status, children, busy,
  startFailed, unavailable, verifying, onStart, resumeRecovery, onResume }: {
  game: GameDef;
  mode: "Jocul zilei" | "Rundă liberă" | "Reluare";
  onExit: () => void;
  help: GameHelpCopy;
  options?: ComponentChildren;
  tools?: ComponentChildren;
  status?: ComponentChildren;
  children?: ComponentChildren;
  busy?: boolean;
  startFailed?: boolean;
  unavailable?: boolean;
  verifying?: boolean;
  onStart?: () => void;
  resumeRecovery?: ResumeRecovery | null;
  onResume?: () => void;
}) {
  const heading = useRef<HTMLHeadingElement>(null);
  const dialog = useRef<HTMLDialogElement>(null);
  const failure = useRef<HTMLDivElement>(null);
  const helpButton = useRef<HTMLButtonElement>(null);
  const helpHeading = useRef<HTMLHeadingElement>(null);
  const [open, setOpen] = useState(false);
  const helpTitle = useId();
  const closeHelp = () => {
    dialog.current?.close();
    setOpen(false);
    const opener = helpButton.current;
    if (opener && !opener.disabled) opener.focus({ preventScroll: true });
    else heading.current?.focus({ preventScroll: true });
  };

  useLayoutEffect(() => { heading.current?.focus({ preventScroll: true }); }, []);
  useLayoutEffect(() => {
    if (!open || !dialog.current) return;
    dialog.current.showModal();
    helpHeading.current?.focus({ preventScroll: true });
  }, [open]);
  useLayoutEffect(() => {
    if (startFailed) failure.current?.scrollIntoView({ block: "nearest", behavior: "instant" });
  }, [startFailed]);

  return (
    <main className={`game-frame game-color-${game.key}`} aria-busy={busy || undefined}>
      <header className="game-frame-band">
        <div className="game-frame-heading">
          <button type="button" className="game-frame-circle" onClick={onExit} disabled={busy} aria-label="Înapoi la jocuri">
            <span aria-hidden="true">‹</span>
          </button>
          <h1 ref={heading} tabIndex={-1}>{game.title}</h1>
          <button ref={helpButton} type="button" className="game-frame-circle" onClick={() => setOpen(true)} disabled={busy}
            aria-label="Cum se joacă" aria-haspopup="dialog">?</button>
        </div>
        <div className="game-frame-status">
          <div>{status}</div>
          <span className="game-frame-mode">{mode}</span>
        </div>
      </header>
      {resumeRecovery && (
        <div className="card game-frame-recovery" role="alert">
          <p>{resumeRecovery.kind === "failed" ? "Nu am putut relua jocul salvat. Nu l-am șters." : "Jocul salvat s-a schimbat în altă filă."}</p>
          {(resumeRecovery.kind === "failed" || resumeRecovery.hasCurrent) &&
            <button type="button" className="btn" onClick={onResume} disabled={busy}>
              {resumeRecovery.kind === "failed" ? "Reîncearcă reluarea" : "Încarcă jocul curent"}
            </button>}
          {!startFailed && (resumeRecovery.kind === "failed" || !resumeRecovery.hasCurrent) &&
            <button type="button" className="btn" onClick={onStart} disabled={busy}>Începe o rundă nouă</button>}
        </div>
      )}
      {startFailed && (
        <div ref={failure} className="card game-frame-recovery" role="alert">
          <p>Nu am putut porni jocul. Am păstrat opțiunile alese. Poți încerca din nou.</p>
          <button type="button" className="btn" onClick={onStart} disabled={busy}>Reîncearcă</button>
        </div>
      )}
      {unavailable && !startFailed && !resumeRecovery && (
        <div className="card game-frame-recovery" role="alert">
          <p>Runda salvată nu mai este disponibilă.</p>
          <button type="button" className="btn" onClick={onStart} disabled={busy}>Începe o rundă nouă</button>
        </div>
      )}
      {verifying && <p className="game-frame-wait" role="status">Se verifică runda salvată…</p>}
      {children}
      {open && (
        <dialog ref={dialog} className="game-help-sheet" aria-labelledby={helpTitle}
          onKeyDown={(event) => {
            if (event.key !== "Tab") return;
            const controls = Array.from(event.currentTarget.querySelectorAll<HTMLElement>("button:not(:disabled), select:not(:disabled)"))
              .filter((control) => control.getClientRects().length > 0);
            const first = controls[0], last = controls[controls.length - 1];
            if (event.shiftKey && (document.activeElement === first || document.activeElement === helpHeading.current)) {
              event.preventDefault();
              last?.focus();
            } else if (!event.shiftKey && document.activeElement === last) {
              event.preventDefault();
              first?.focus();
            }
          }}
          onCancel={(event) => { event.preventDefault(); closeHelp(); }}>
          <div className="game-help-heading">
            <h2 id={helpTitle} ref={helpHeading} tabIndex={-1}>Cum se joacă {game.title}</h2>
            <button type="button" className="game-frame-circle" aria-label="Închide ajutorul"
              onClick={closeHelp}>×</button>
          </div>
          <ol className="game-help-instructions">
            <li>{help.goal}</li>
            <li>{help.feedback}</li>
            <li>{help.recovery}</li>
          </ol>
          <h3>Indiciile</h3>
          <ol className="game-help-ladder">{help.ladder.map((rung) => <li key={rung}>{rung}</li>)}</ol>
          <p>Un indiciu costă un pas. Nu pierzi nicio încercare.</p>
          <h3>Cum se numără pașii</h3>
          <p>{help.steps}</p>
          {options && <section className="game-help-options"><h3>Opțiuni pentru următoarea rundă liberă</h3>{options}</section>}
          <button type="button" className="btn game-help-confirm" onClick={closeHelp}>Am înțeles</button>
          {tools && <form method="dialog">{tools}</form>}
        </dialog>
      )}
    </main>
  );
}

/** Replaces the content inside a mounted live region even when the new text is identical. */
export function CoachLine({ children, revision, id }: {
  children?: ComponentChildren;
  revision?: number;
  id?: string;
}) {
  return (
    <div className="coach-line" role="status" aria-atomic="true" id={id}>
      {children && <span key={revision}>{children}</span>}
    </div>
  );
}

export function Attempts({ remaining }: { remaining: number }) {
  return <span>{remaining === 1 ? "O încercare" : `${remaining} încercări`}</span>;
}
