import type { GameKey } from "./games";

export const GAME_HELP: Readonly<Record<GameKey, {
  readonly goal: string;
  readonly feedback: string;
  readonly recovery: string;
}>>;
