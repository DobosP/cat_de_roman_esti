import type { ReactNode } from "react";
import type { GameKey } from "../games";
import { GameHelp } from "./GameHelp";
import "../styles/game-options.css";

/** Optional tools stay available without occupying the main play area. */
export function GameOptions({ game, help = true, children }: { game: GameKey; help?: boolean; children?: ReactNode }) {
  return (
    <>
      {help && <GameHelp game={game} />}
      {children && (
        <details className="game-options">
          <summary>Opțiuni de joc</summary>
          <div className="game-options-content">{children}</div>
        </details>
      )}
    </>
  );
}
