import type { GameKey } from "./games";

export interface GameHelpCopy {
  readonly goal: string;
  readonly feedback: string;
  readonly recovery: string;
}

export const GAME_HELP: Readonly<Record<GameKey, GameHelpCopy>>;
