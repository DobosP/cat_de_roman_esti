import type { GameKey } from "./games";

export interface GameHelpCopy {
  readonly goal: string;
  readonly feedback: string;
  readonly recovery: string;
  readonly ladder: readonly string[];
  readonly steps: string;
}

export const GAME_HELP: Readonly<Record<GameKey, GameHelpCopy>>;
