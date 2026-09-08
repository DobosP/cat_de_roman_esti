import { acquireFlight, recoverAuthoritative, releaseFlight } from "./asyncControl.mjs";

/** One action ticket owns callbacks only while its screen and saved pointer still match. */
export function createGameActionOwner(active) {
  const lock = { current: false };
  let pending = null;
  return {
    begin(gameId) {
      if (!gameId || !acquireFlight(lock)) return null;
      pending = Object.freeze({ gameId, savedId: active.peek() });
      return pending;
    },
    isCurrent(ticket) {
      return pending === ticket;
    },
    owns(ticket) {
      if (pending !== ticket) return false;
      // Storage can be unavailable. A locally owned round remains playable while
      // both observations are null; a different remembered round always wins.
      return ticket.savedId === ticket.gameId
        ? active.isCurrent(ticket.gameId)
        : ticket.savedId === null && active.peek() === null;
    },
    finish(ticket) {
      if (pending !== ticket) return false;
      pending = null;
      releaseFlight(lock);
      return true;
    },
    hasPending() {
      return pending !== null;
    },
    invalidate() {
      pending = null;
      releaseFlight(lock);
    },
  };
}

/** Read once after uncertainty; this helper has no mutation or replay callback. */
export async function recoverOwnedGameAction(owner, ticket, load, isMissing = () => false) {
  if (!owner.isCurrent(ticket)) return { kind: "stale" };
  if (!owner.owns(ticket)) return { kind: "changed" };
  let missing = false;
  const result = await recoverAuthoritative(async () => {
    try {
      return await load(ticket.gameId);
    } catch (error) {
      missing = isMissing(error);
      throw error;
    }
  });
  if (!owner.isCurrent(ticket)) return { kind: "stale" };
  if (!owner.owns(ticket)) return { kind: "changed" };
  if (!result.ok) return { kind: missing ? "missing" : "failed" };
  if (result.value?.game_id !== ticket.gameId) return { kind: "failed" };
  return { kind: "recovered", state: result.value };
}
