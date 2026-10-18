import type { ComponentChildren } from "preact";
import type { GameHelpCopy } from "../gameHelp.mjs";
import { GameHelp } from "./GameHelp";
import "../styles/game-options.css";

/** Optional tools stay available without occupying the main play area. */
export function GameOptions({ help, children }: { help?: GameHelpCopy; children?: ComponentChildren }) {
  return (
    <>
      {help && <GameHelp help={help} />}
      {children && (
        <details className="game-options">
          <summary>Opțiuni de joc</summary>
          <div className="game-options-content">{children}</div>
        </details>
      )}
    </>
  );
}
