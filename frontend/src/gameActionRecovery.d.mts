export interface GameActionTicket {
  readonly gameId: string;
  readonly savedId: string | null;
}

export interface GameActionOwner {
  begin(gameId: string): GameActionTicket | null;
  isCurrent(ticket: GameActionTicket): boolean;
  owns(ticket: GameActionTicket): boolean;
  finish(ticket: GameActionTicket): boolean;
  hasPending(): boolean;
  invalidate(): void;
}

export function createGameActionOwner(active: {
  peek(): string | null;
  isCurrent(gameId: string): boolean;
}): GameActionOwner;

export function recoverOwnedGameAction<T extends { game_id: string }>(
  owner: GameActionOwner,
  ticket: GameActionTicket,
  load: (gameId: string) => Promise<T>,
  isMissing?: (error: unknown) => boolean,
): Promise<
  | { kind: "stale" | "changed" | "failed" | "missing" }
  | { kind: "recovered"; state: T }
>;
