export interface FlightLock {
  current: boolean;
}

export function acquireFlight(lock: FlightLock): boolean;
export function releaseFlight(lock: FlightLock): void;

export type AuthoritativeRecovery<T> =
  | { ok: true; value: T }
  | { ok: false; value: null };

export function recoverAuthoritative<T>(
  load: () => Promise<T>,
): Promise<AuthoritativeRecovery<T>>;
