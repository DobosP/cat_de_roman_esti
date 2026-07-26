/** Acquire a synchronous single-flight lock before React has time to re-render. */
export function acquireFlight(lock) {
  if (lock.current) return false;
  lock.current = true;
  return true;
}

/** Release a lock acquired with acquireFlight. */
export function releaseFlight(lock) {
  lock.current = false;
}

/**
 * Try to recover the latest server-authored state after an ambiguous mutation failure.
 * The caller decides how to render it; failures intentionally carry no stale substitute.
 */
export async function recoverAuthoritative(load) {
  try {
    return { ok: true, value: await load() };
  } catch {
    return { ok: false, value: null };
  }
}
