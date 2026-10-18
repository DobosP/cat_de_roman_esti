import { batch, useSignal } from "@preact/signals";
import { useCallback, useMemo } from "preact/hooks";

type Update<T> = T | ((previous: T) => T);
/** Component-local signals with render snapshots for existing async action tickets. */
export function useSignalState<T>(initial: T | (() => T)): [T, (update: Update<T>) => void] {
  const seed = useMemo(() => typeof initial === "function" ? (initial as () => T)() : initial, []);
  const value = useSignal<T>(seed);
  const setValue = useCallback((update: Update<T>) => batch(() => {
    value.value = typeof update === "function" ? (update as (previous: T) => T)(value.peek()) : update;
  }), [value]);
  return [value.value, setValue];
}
