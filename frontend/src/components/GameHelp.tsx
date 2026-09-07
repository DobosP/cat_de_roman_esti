import type { GameKey } from "../games";
import { GAME_HELP } from "../gameHelp.mjs";

export function GameHelp({ game }: { game: GameKey }) {
  const help = GAME_HELP[game];
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
