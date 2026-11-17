// Page-lifetime fallback for optional browser storage. Failed writes take
// precedence over stale disk values until an explicit write succeeds.
const values = new Map<string, string | null>();
const unsaved = new Set<string>();

export function readLocalValue(key: string): string | null {
  if (unsaved.has(key)) return values.get(key) ?? null;
  try {
    const value = localStorage.getItem(key);
    values.set(key, value);
    return value;
  } catch {
    return values.get(key) ?? null;
  }
}

export function writeLocalValue(key: string, value: string | null): void {
  values.set(key, value);
  try {
    if (value === null) localStorage.removeItem(key);
    else localStorage.setItem(key, value);
    unsaved.delete(key);
  } catch {
    unsaved.add(key);
  }
}
