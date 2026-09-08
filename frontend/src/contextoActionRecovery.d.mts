export interface ContextoActionTicket {
  readonly gameId: string;
  readonly savedId: string | null;
}

export interface ContextoActionOwner {
  begin(gameId: string): ContextoActionTicket | null;
  isCurrent(ticket: ContextoActionTicket): boolean;
  owns(ticket: ContextoActionTicket): boolean;
  finish(ticket: ContextoActionTicket): boolean;
  hasPending(): boolean;
  invalidate(): void;
}

export function createContextoActionOwner(active: {
  peek(): string | null;
  isCurrent(gameId: string): boolean;
}): ContextoActionOwner;

export function recoverOwnedContextoAction<T extends { game_id: string }>(
  owner: ContextoActionOwner,
  ticket: ContextoActionTicket,
  load: (gameId: string) => Promise<T>,
  isMissing?: (error: unknown) => boolean,
): Promise<
  | { kind: "stale" | "changed" | "failed" | "missing" }
  | { kind: "recovered"; state: T }
>;
