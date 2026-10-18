import type { GameHelpCopy } from "../gameHelp.mjs";

export function GameHelp({ help }: { help: GameHelpCopy }) {
  return (
    <details className="game-help">
      <summary>Reguli și ajutor</summary>
      <dl className="game-help-copy">
        <dt>Ce urmărești</dt>
        <dd>{help.goal}</dd>
        <dt>Cum citești răspunsul</dt>
        <dd>{help.feedback}</dd>
        <dt>Dacă te blochezi</dt>
        <dd>{help.recovery}</dd>
      </dl>
      <p className="faint game-help-note">Citirea regulilor nu folosește un indiciu și nu schimbă scorul.</p>
    </details>
  );
}
